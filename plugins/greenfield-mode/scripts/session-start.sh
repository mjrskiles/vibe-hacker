#!/bin/bash
# session-start.sh
# Prints greenfield mode status on session start
#
# Exit codes:
#   0 - Always (informational only)

set -euo pipefail

CONFIG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/vibe-hacker.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if greenfield mode is enabled
is_greenfield_enabled() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local enabled
        enabled=$(jq -r '.greenfield_mode // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
        [[ "$enabled" == "true" ]]
    else
        return 1
    fi
}

# Check if strict mode is enabled
is_strict_mode() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local strict
        strict=$(jq -r '.greenfield_strict // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
        [[ "$strict" == "true" ]]
    else
        return 1
    fi
}

main() {
    if is_greenfield_enabled; then
        echo "" >&2
        echo -e "${GREEN}GREENFIELD MODE${NC} ${CYAN}enabled${NC}" >&2
        if is_strict_mode; then
            echo -e "  ${YELLOW}Strict mode: ON${NC} - cruft will block edits" >&2
        else
            echo -e "  Strict mode: off - cruft will warn only" >&2
        fi
        echo -e "  No backwards compatibility needed. Delete, don't deprecate." >&2
        echo "" >&2
    fi

    exit 0
}

main "$@"
