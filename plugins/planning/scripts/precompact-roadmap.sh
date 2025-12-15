#!/usr/bin/env bash
#
# PreCompact hook: Remind to update roadmap before context compaction
#

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
CONFIG_FILE="$PROJECT_DIR/.claude/vibe-hacker.json"

# Get planning root from config, default to docs/planning
PLANNING_ROOT="docs/planning"
if [[ -f "$CONFIG_FILE" ]] && command -v jq &>/dev/null; then
    configured_root=$(jq -r '.protected_paths.planning_root // empty' "$CONFIG_FILE" 2>/dev/null || true)
    if [[ -n "$configured_root" ]]; then
        PLANNING_ROOT="$configured_root"
    fi
fi

ROADMAP_FILE="$PROJECT_DIR/$PLANNING_ROOT/roadmap.md"

# Only remind if roadmap exists
if [[ -f "$ROADMAP_FILE" ]]; then
    # Display to user terminal (stderr)
    echo "ROADMAP UPDATE REMINDER - Review before compaction" >&2

    # Inject reminder into Claude's context (stdout JSON)
    context="ROADMAP UPDATE REMINDER: Before context compaction, please review and update the project roadmap at $PLANNING_ROOT/roadmap.md:

1. Move completed items to 'Recently Completed' section
2. Update 'Immediate' goals based on current progress
3. Adjust priorities in 'Medium Term' and 'Long Term' as needed
4. Update the 'Last updated' date"

    context=$(echo "$context" | jq -Rs '.')

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreCompact",
    "additionalContext": ${context}
  }
}
EOF
fi

exit 0
