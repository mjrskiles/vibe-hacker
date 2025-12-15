#!/bin/bash
# prime.sh - Context priming for Claude Code sessions
#
# Loads project context from .claude/vibe-hacker.json config.
# Falls back to README.md / CLAUDE.md if no config.
#
# Output strategy:
# - stderr: Priming display (for user's terminal)
# - stdout: JSON with additionalContext (for Claude's context injection)

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$PROJECT_DIR"

CONFIG_FILE=".claude/vibe-hacker.json"

# Collect files to load
declare -a FILES=()
INSTRUCTIONS=""

# Check greenfield mode (play nice with greenfield plugin if installed)
GREENFIELD="disabled"
if [[ -f "$CONFIG_FILE" ]]; then
    gf=$(jq -r '.greenfield_mode // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
    [[ "$gf" == "true" ]] && GREENFIELD="enabled"
fi

# Check haiku mode
HAIKU="disabled"
if [[ -f "$CONFIG_FILE" ]]; then
    hk=$(jq -r '.priming.haiku // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
    [[ "$hk" == "true" ]] && HAIKU="enabled"
fi

# Load priming config
if [[ -f "$CONFIG_FILE" ]]; then
    # Get instructions
    INSTRUCTIONS=$(jq -r '.priming.instructions // empty' "$CONFIG_FILE" 2>/dev/null || true)

    # Get explicit files
    while IFS= read -r file; do
        [[ -n "$file" && -f "$file" ]] && FILES+=("$file")
    done < <(jq -r '.priming.files[]? // empty' "$CONFIG_FILE" 2>/dev/null || true)

    # Expand globs
    while IFS= read -r pattern; do
        if [[ -n "$pattern" ]]; then
            for file in $pattern; do
                [[ -f "$file" ]] && FILES+=("$file")
            done
        fi
    done < <(jq -r '.priming.globs[]? // empty' "$CONFIG_FILE" 2>/dev/null || true)
fi

# Fallback if no files configured
if [[ ${#FILES[@]} -eq 0 ]]; then
    [[ -f ".claude/CLAUDE.md" ]] && FILES+=(".claude/CLAUDE.md")
    [[ -f "README.md" ]] && FILES+=("README.md")

    # Last resort: scan docs/
    if [[ ${#FILES[@]} -eq 0 && -d "docs" ]]; then
        while IFS= read -r file; do
            FILES+=("$file")
        done < <(find docs -name "*.md" -type f 2>/dev/null | head -5)
    fi
fi

# Remove duplicates
declare -A seen
UNIQUE=()
for f in "${FILES[@]}"; do
    if [[ -z "${seen[$f]:-}" ]]; then
        seen[$f]=1
        UNIQUE+=("$f")
    fi
done

# Display to stderr (user sees this in terminal)
{
    echo "=== CONTEXT PRIMING ==="
    echo ""

    if [[ "$GREENFIELD" == "enabled" ]]; then
        echo "Greenfield mode: ENABLED"
        echo ""
    fi

    if [[ "$HAIKU" == "enabled" ]]; then
        echo "Haiku mode: ENABLED"
        echo ""
    fi

    if [[ -n "$INSTRUCTIONS" ]]; then
        echo "Instructions: $INSTRUCTIONS"
        echo ""
    fi

    echo "Loading ${#UNIQUE[@]} files: ${UNIQUE[*]}"
    echo ""
    echo "=== END PRIMING ==="
} >&2

# Build context for Claude (stdout as JSON)
# Include file contents and haiku request in additionalContext
CONTEXT_PARTS=()

if [[ "$GREENFIELD" == "enabled" ]]; then
    CONTEXT_PARTS+=("GREENFIELD MODE: This is a prototype project with zero users. Delete old code entirely, no backwards compatibility needed, no deprecation comments.")
fi

if [[ -n "$INSTRUCTIONS" ]]; then
    CONTEXT_PARTS+=("INSTRUCTIONS: $INSTRUCTIONS")
fi

# Add file contents
for file in "${UNIQUE[@]}"; do
    # Read file and escape for JSON
    content=$(cat "$file" | jq -Rs '.')
    CONTEXT_PARTS+=("FILE: $file
${content}")
done

if [[ "$HAIKU" == "enabled" ]]; then
    CONTEXT_PARTS+=("HAIKU REQUEST: Please write a creative haiku (5-7-5 syllables) that captures the essence of this project based on the primed content above. This confirms you are ready.")
fi

# Join parts with newlines and escape for JSON
FULL_CONTEXT=$(printf '%s\n\n' "${CONTEXT_PARTS[@]}" | jq -Rs '.')

# Output JSON to stdout for Claude Code to parse
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ${FULL_CONTEXT}
  }
}
EOF
