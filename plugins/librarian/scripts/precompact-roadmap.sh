#!/usr/bin/env bash
#
# PreCompact hook: remind to update the roadmap before context compaction.
#
# Fires only for a roadmap that is actually being maintained: its own
# "> Last updated: YYYY-MM-DD" line (the librarian template convention) is within
# ACTIVE_DAYS. Without that line, fall back to git history, then mtime. A roadmap
# nobody has touched in months is a fossil, and nagging about it every compaction
# is noise — and a bulk reformat commit doesn't count as maintenance.
#

set -euo pipefail

ACTIVE_DAYS=30

# Config resolution: prefer CLAUDE_PROJECT_DIR, fall back to git root
find_config() {
    if [[ -n "${CLAUDE_PROJECT_DIR:-}" && -f "$CLAUDE_PROJECT_DIR/.claude/vibe-hacker.json" ]]; then
        echo "$CLAUDE_PROJECT_DIR/.claude/vibe-hacker.json"
        return
    fi
    local git_root
    git_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [[ -n "$git_root" && -f "$git_root/.claude/vibe-hacker.json" ]]; then
        echo "$git_root/.claude/vibe-hacker.json"
        return
    fi
    echo ".claude/vibe-hacker.json"
}

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
CONFIG_FILE=$(find_config)

# Get planning root from config, default to docs/planning
PLANNING_ROOT="docs/planning"
if [[ -f "$CONFIG_FILE" ]] && command -v jq &>/dev/null; then
    configured_root=$(jq -r '.protected_paths.planning_root // empty' "$CONFIG_FILE" 2>/dev/null || true)
    if [[ -n "$configured_root" ]]; then
        PLANNING_ROOT="$configured_root"
    fi
fi

ROADMAP_FILE="$PROJECT_DIR/$PLANNING_ROOT/roadmap.md"

[[ -f "$ROADMAP_FILE" ]] || exit 0

# Epoch seconds of the roadmap's last maintenance.
last_changed() {
    local stamped
    stamped=$(grep -m1 -oE '^> Last updated: *[0-9]{4}-[0-9]{2}-[0-9]{2}' "$ROADMAP_FILE" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || true)
    if [[ -n "$stamped" ]] && date -d "$stamped" +%s &>/dev/null; then
        date -d "$stamped" +%s
        return
    fi
    # No stamp: uncommitted edits count as now, else last commit, else mtime.
    if git -C "$(dirname "$ROADMAP_FILE")" rev-parse --is-inside-work-tree &>/dev/null; then
        if [[ -n "$(git -C "$(dirname "$ROADMAP_FILE")" status --porcelain -- "$(basename "$ROADMAP_FILE")" 2>/dev/null)" ]]; then
            date +%s
            return
        fi
        local committed
        committed=$(git -C "$(dirname "$ROADMAP_FILE")" log -1 --format=%ct -- "$(basename "$ROADMAP_FILE")" 2>/dev/null || true)
        if [[ -n "$committed" ]]; then
            echo "$committed"
            return
        fi
    fi
    stat -c %Y "$ROADMAP_FILE" 2>/dev/null || stat -f %m "$ROADMAP_FILE"
}

age_days=$(( ( $(date +%s) - $(last_changed) ) / 86400 ))
[[ "$age_days" -le "$ACTIVE_DAYS" ]] || exit 0

echo "ROADMAP UPDATE REMINDER - Review before compaction" >&2

# Inject reminder via systemMessage (PreCompact has no hookSpecificOutput support)
context="ROADMAP UPDATE REMINDER: Before context compaction, please review and update the project roadmap at $PLANNING_ROOT/roadmap.md:\n\n1. Move completed items to 'Recently Completed' section\n2. Update 'Immediate' goals based on current progress\n3. Adjust priorities in 'Medium Term' and 'Long Term' as needed\n4. Update the 'Last updated' date"
context=$(echo -e "$context" | jq -Rs '.')

cat <<JSON
{
  "systemMessage": ${context}
}
JSON
