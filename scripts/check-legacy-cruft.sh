#!/bin/bash
# check-legacy-cruft.sh
# Detects backwards-compatibility cruft that shouldn't exist in a greenfield project
#
# Usage:
#   - As a hook: receives JSON on stdin with tool_input.file_path
#   - Direct: ./check-legacy-cruft.sh [file_path]
#   - No args: checks git diff for modified files
#   - --warn-only: warn but don't block (exit 0 even if cruft found)
#
# Exit codes:
#   0 - No legacy cruft found (or --warn-only mode)
#   1 - Error (missing file, etc)
#   2 - Legacy cruft detected (blocks hook if used with PreToolUse/PostToolUse)

set -euo pipefail

WARN_ONLY=false
if [[ "${1:-}" == "--warn-only" ]]; then
    WARN_ONLY=true
    shift
fi

# Patterns that indicate legacy/deprecation cruft
CRUFT_PATTERNS=(
    '// deprecated'
    '// legacy'
    '// old:'
    '// old way'
    '// TODO: remove after migration'
    '// TODO: remove when'
    '// backwards compat'
    '// backward compat'
    '// for compatibility'
    '// kept for compatibility'
    '// DEPRECATED'
    '@deprecated'
    '# deprecated'
    '# legacy'
    '# old:'
    '# TODO: remove after migration'
    '# backwards compat'
    '# for compatibility'
)

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file="$1"
    local found_cruft=0

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    # Skip binary files and common non-code files
    if file "$file" | grep -q "binary\|executable\|image\|archive"; then
        return 0
    fi

    for pattern in "${CRUFT_PATTERNS[@]}"; do
        if grep -qi "$pattern" "$file" 2>/dev/null; then
            if [[ $found_cruft -eq 0 ]]; then
                echo -e "${YELLOW}Legacy cruft detected in: $file${NC}" >&2
                found_cruft=1
            fi
            echo -e "  ${RED}→${NC} Found pattern: '$pattern'" >&2
            grep -n -i "$pattern" "$file" 2>/dev/null | head -3 | sed 's/^/    /' >&2
        fi
    done

    return $found_cruft
}

main() {
    local files_to_check=()
    local exit_code=0

    # Determine which files to check
    if [[ $# -gt 0 ]]; then
        # Direct invocation with file path
        files_to_check=("$@")
    elif [[ ! -t 0 ]]; then
        # Reading from stdin (hook mode)
        local input
        input=$(cat)

        # Try to extract file_path from JSON (for PostToolUse on Edit/Write)
        local file_path
        file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)

        if [[ -n "$file_path" && -f "$file_path" ]]; then
            files_to_check=("$file_path")
        else
            # For Stop hook, check recently modified files in project
            if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
                # Check uncommitted changes
                while IFS= read -r file; do
                    [[ -f "$file" ]] && files_to_check+=("$file")
                done < <(git diff --name-only 2>/dev/null || true)

                # Also check staged files
                while IFS= read -r file; do
                    [[ -f "$file" ]] && files_to_check+=("$file")
                done < <(git diff --cached --name-only 2>/dev/null || true)
            fi
        fi
    else
        # No input, check git changes
        if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
            while IFS= read -r file; do
                [[ -f "$file" ]] && files_to_check+=("$file")
            done < <(git diff --name-only 2>/dev/null || true)
        fi
    fi

    # Remove duplicates
    local unique_files=()
    declare -A seen
    for file in "${files_to_check[@]}"; do
        if [[ -z "${seen[$file]:-}" ]]; then
            seen[$file]=1
            unique_files+=("$file")
        fi
    done

    # Check each file
    local cruft_found=0
    for file in "${unique_files[@]}"; do
        if ! check_file "$file"; then
            cruft_found=1
        fi
    done

    if [[ $cruft_found -eq 1 ]]; then
        echo "" >&2
        echo -e "${YELLOW}⚠️  REMINDER: This is a greenfield project with no users.${NC}" >&2
        echo -e "${YELLOW}   Please remove deprecated/legacy comments and code.${NC}" >&2
        echo -e "${YELLOW}   There is no 'old way' to document.${NC}" >&2

        if [[ "$WARN_ONLY" == "true" ]]; then
            # Warn but don't block
            cat << 'EOF'
{
    "decision": "approve",
    "reason": "Legacy cruft detected (warning only). Please clean up deprecated comments."
}
EOF
            exit 0
        else
            # Block the operation
            cat << 'EOF'
{
    "decision": "block",
    "reason": "Legacy cruft detected. This is a greenfield project - please remove deprecated comments and backwards-compatibility code."
}
EOF
            exit 2
        fi
    fi

    # Success - output approval for hook system
    cat << 'EOF'
{
    "decision": "approve",
    "reason": "No legacy cruft detected"
}
EOF
    exit 0
}

main "$@"
