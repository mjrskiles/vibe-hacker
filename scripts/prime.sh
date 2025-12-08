#!/bin/bash
# prime.sh
# Context priming script for Claude Code sessions
#
# Usage:
#   prime.sh --light    # Light priming (SessionStart) - instructions only
#   prime.sh --full     # Full priming (/prime command) - read all files
#   prime.sh --check    # Just check what would be primed (dry run)
#
# Config location: .claude/firmware-hacker.json
# Fallback chain:
#   1. .claude/firmware-hacker.json (if exists, use priming config)
#   2. .claude/CLAUDE.md (if no config)
#   3. README.md (if no CLAUDE.md)
#   4. docs/ directory (scan for key files)
#
# firmware-hacker.json format:
# {
#   "greenfield_mode": true,
#   "priming": {
#     "files": ["README.md", "docs/ARCHITECTURE.md"],
#     "globs": ["docs/planning/action-plans/*.md"],
#     "instructions": "Custom priming instructions..."
#   }
# }

set -euo pipefail

MODE="full"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --light) MODE="light"; shift ;;
        --full) MODE="full"; shift ;;
        --check) MODE="check"; shift ;;
        --project-dir) PROJECT_DIR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

cd "$PROJECT_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CONFIG_JSON=".claude/firmware-hacker.json"
CLAUDE_MD=".claude/CLAUDE.md"
README="README.md"
DOCS_DIR="docs"

# Collect files to prime
declare -a FILES_TO_READ=()
INSTRUCTIONS=""

log() {
    echo -e "$1" >&2
}

read_file_content() {
    local file="$1"
    if [[ -f "$file" ]]; then
        echo ""
        echo "=== FILE: $file ==="
        cat "$file"
        echo ""
        echo "=== END: $file ==="
        echo ""
    fi
}

list_file() {
    local file="$1"
    log "  ${GREEN}→${NC} $file"
}

# Check greenfield status for reporting
GREENFIELD_MODE="disabled"
if [[ -f "$CONFIG_JSON" ]]; then
    gf_enabled=$(jq -r '.greenfield_mode // false' "$CONFIG_JSON" 2>/dev/null || echo "false")
    [[ "$gf_enabled" == "true" ]] && GREENFIELD_MODE="enabled"
fi

# Strategy 1: Use firmware-hacker.json if it exists
if [[ -f "$CONFIG_JSON" ]]; then
    log "${CYAN}Found firmware-hacker.json - using configured priming${NC}"

    # Extract instructions from priming section
    INSTRUCTIONS=$(jq -r '.priming.instructions // empty' "$CONFIG_JSON" 2>/dev/null || true)

    # Extract explicit files from priming section
    while IFS= read -r file; do
        [[ -n "$file" && -f "$file" ]] && FILES_TO_READ+=("$file")
    done < <(jq -r '.priming.files[]? // empty' "$CONFIG_JSON" 2>/dev/null || true)

    # Expand globs from priming section
    while IFS= read -r pattern; do
        if [[ -n "$pattern" ]]; then
            for file in $pattern; do
                [[ -f "$file" ]] && FILES_TO_READ+=("$file")
            done
        fi
    done < <(jq -r '.priming.globs[]? // empty' "$CONFIG_JSON" 2>/dev/null || true)

# Strategy 2: Fall back to CLAUDE.md
elif [[ -f "$CLAUDE_MD" ]]; then
    log "${CYAN}No firmware-hacker.json - falling back to CLAUDE.md${NC}"
    FILES_TO_READ+=("$CLAUDE_MD")

    # Also grab README if it exists
    [[ -f "$README" ]] && FILES_TO_READ+=("$README")

# Strategy 3: Fall back to README.md
elif [[ -f "$README" ]]; then
    log "${CYAN}No CLAUDE.md - falling back to README.md${NC}"
    FILES_TO_READ+=("$README")

# Strategy 4: Scan docs/ directory
elif [[ -d "$DOCS_DIR" ]]; then
    log "${CYAN}No README.md - scanning docs/ directory${NC}"
    while IFS= read -r file; do
        FILES_TO_READ+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f 2>/dev/null | head -10)
else
    log "${YELLOW}No priming sources found. Consider creating:${NC}"
    log "  - .claude/firmware-hacker.json (recommended)"
    log "  - .claude/CLAUDE.md"
    log "  - README.md"
fi

# Remove duplicates while preserving order
declare -A seen
UNIQUE_FILES=()
for file in "${FILES_TO_READ[@]}"; do
    if [[ -z "${seen[$file]:-}" ]]; then
        seen[$file]=1
        UNIQUE_FILES+=("$file")
    fi
done

# Execute based on mode
case $MODE in
    check)
        log ""
        log "${CYAN}Files that would be primed:${NC}"
        for file in "${UNIQUE_FILES[@]}"; do
            list_file "$file"
        done
        if [[ -n "$INSTRUCTIONS" ]]; then
            log ""
            log "${CYAN}Instructions:${NC}"
            log "  $INSTRUCTIONS"
        fi
        ;;

    light)
        # Light mode: Just output instructions and file list
        echo "=== CONTEXT PRIMING (Light) ==="
        echo ""
        echo "Greenfield mode: $GREENFIELD_MODE"
        echo ""
        if [[ -n "$INSTRUCTIONS" ]]; then
            echo "PRIMING INSTRUCTIONS: $INSTRUCTIONS"
            echo ""
        fi
        echo "The following files are available for full context priming:"
        for file in "${UNIQUE_FILES[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Use /prime command to load full file contents if needed."
        echo "=== END PRIMING ==="
        ;;

    full)
        # Full mode: Output all file contents
        echo "=== CONTEXT PRIMING (Full) ==="
        echo ""
        echo "Greenfield mode: $GREENFIELD_MODE"
        echo ""
        if [[ -n "$INSTRUCTIONS" ]]; then
            echo "PRIMING INSTRUCTIONS: $INSTRUCTIONS"
            echo ""
        fi
        echo "Loading ${#UNIQUE_FILES[@]} files for context..."
        echo ""

        for file in "${UNIQUE_FILES[@]}"; do
            read_file_content "$file"
        done

        echo "=== END PRIMING ==="
        echo ""
        echo "Context has been primed with ${#UNIQUE_FILES[@]} files."
        ;;
esac
