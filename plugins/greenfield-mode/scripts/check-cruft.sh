#!/bin/bash
# check-cruft.sh
# Detects backwards-compatibility cruft in greenfield projects
#
# Usage:
#   - As PostToolUse hook: receives JSON on stdin with tool_input.file_path
#   - Direct: ./check-cruft.sh [file_path]
#
# Exit codes:
#   0 - No cruft found or greenfield mode disabled (approve)
#   2 - Cruft detected (warn but approve - greenfield is advisory)

set -euo pipefail

CONFIG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/vibe-hacker.json"

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

# Check if strict mode is enabled (block instead of warn)
is_strict_mode() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local strict
        strict=$(jq -r '.greenfield_strict // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
        [[ "$strict" == "true" ]]
    else
        return 1
    fi
}

# Exit early if greenfield mode not enabled
if ! is_greenfield_enabled; then
    echo '{"decision": "approve", "reason": "Greenfield mode not enabled"}'
    exit 0
fi

# Default cruft patterns
DEFAULT_PATTERNS=(
    '// deprecated'
    '// legacy'
    '// old:'
    '// TODO: remove after migration'
    '// backwards compat'
    '// for compatibility'
    '@deprecated'
    '# deprecated'
    '# legacy'
    '# TODO: remove after migration'
)

# Load custom patterns from config or use defaults
load_patterns() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local patterns_json
        patterns_json=$(jq -r '.greenfield_patterns // empty' "$CONFIG_FILE" 2>/dev/null || true)

        if [[ -n "$patterns_json" && "$patterns_json" != "null" ]]; then
            local patterns=()
            while IFS= read -r pattern; do
                [[ -n "$pattern" ]] && patterns+=("$pattern")
            done < <(echo "$patterns_json" | jq -r '.[]' 2>/dev/null)

            if [[ ${#patterns[@]} -gt 0 ]]; then
                CRUFT_PATTERNS=("${patterns[@]}")
                return
            fi
        fi
    fi
    CRUFT_PATTERNS=("${DEFAULT_PATTERNS[@]}")
}

load_patterns

# Colors
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

check_file() {
    local file="$1"
    local found=0

    [[ ! -f "$file" ]] && return 0

    # Skip binary files
    if file "$file" 2>/dev/null | grep -q "binary\|executable\|image"; then
        return 0
    fi

    for pattern in "${CRUFT_PATTERNS[@]}"; do
        if grep -qi "$pattern" "$file" 2>/dev/null; then
            if [[ $found -eq 0 ]]; then
                echo -e "${YELLOW}Cruft detected in: $file${NC}" >&2
                found=1
            fi
            echo -e "  ${RED}→${NC} '$pattern'" >&2
            grep -n -i "$pattern" "$file" 2>/dev/null | head -2 | sed 's/^/    /' >&2
        fi
    done

    return $found
}

main() {
    local file_path=""

    # Get file from args or stdin JSON
    if [[ $# -gt 0 ]]; then
        file_path="$1"
    elif [[ ! -t 0 ]]; then
        local input
        input=$(cat)
        file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
    fi

    if [[ -z "$file_path" || ! -f "$file_path" ]]; then
        echo '{"decision": "approve", "reason": "No file to check"}'
        exit 0
    fi

    if ! check_file "$file_path"; then
        echo "" >&2
        echo -e "${YELLOW}GREENFIELD REMINDER: No backwards compatibility needed.${NC}" >&2
        echo -e "${YELLOW}Delete deprecated code, don't comment it.${NC}" >&2

        if is_strict_mode; then
            echo '{"decision": "block", "reason": "Cruft detected in greenfield project. Remove deprecated/legacy patterns before continuing."}'
            exit 2
        else
            echo '{"decision": "approve", "reason": "Cruft detected - please clean up (warning only)"}'
            exit 0
        fi
    fi

    echo '{"decision": "approve", "reason": "No cruft detected"}'
    exit 0
}

main "$@"
