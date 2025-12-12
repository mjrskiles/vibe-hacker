#!/bin/bash
# prime.sh - Context priming for Claude Code sessions
#
# Loads project context from .claude/vibe-hacker.json config.
# Falls back to README.md / CLAUDE.md if no config.
#
# Config format:
# {
#   "priming": {
#     "files": ["README.md", "docs/ARCHITECTURE.md"],
#     "globs": ["docs/planning/**/*.md"],
#     "instructions": "Custom instructions..."
#   }
# }

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

# Output
echo "=== CONTEXT PRIMING ==="
echo ""

if [[ "$GREENFIELD" == "enabled" ]]; then
    echo "Greenfield mode: ENABLED"
    echo ""
    echo "REMINDER: This is a prototype project with no users."
    echo "- Delete old code, don't comment it out"
    echo "- No backwards compatibility needed"
    echo "- No deprecation comments"
    echo ""
fi

if [[ -n "$INSTRUCTIONS" ]]; then
    echo "INSTRUCTIONS: $INSTRUCTIONS"
    echo ""
fi

echo "Loading ${#UNIQUE[@]} files..."
echo ""

for file in "${UNIQUE[@]}"; do
    echo "=== FILE: $file ==="
    cat "$file"
    echo ""
    echo "=== END: $file ==="
    echo ""
done

echo "=== END PRIMING ==="
