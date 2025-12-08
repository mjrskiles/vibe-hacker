#!/bin/bash
# greenfield-stop-hook.sh
# Conditional Stop hook for greenfield mode
# Outputs approval JSON - greenfield review is informational only

set -euo pipefail

config_file="${CLAUDE_PROJECT_DIR:-.}/.claude/firmware-hacker.json"

# Check if greenfield mode is enabled
if [[ -f "$config_file" ]]; then
    enabled=$(jq -r '.greenfield_mode // false' "$config_file" 2>/dev/null || echo "false")
    if [[ "$enabled" == "true" ]]; then
        # Greenfield mode enabled - remind about greenfield rules
        cat << 'EOF'
{
    "decision": "approve",
    "reason": "GREENFIELD MODE ACTIVE: Remember - no backwards compatibility shims, no deprecation comments, delete unused code entirely."
}
EOF
        exit 0
    fi
fi

# Greenfield mode not enabled - silent approval
cat << 'EOF'
{
    "decision": "approve",
    "reason": "Greenfield mode not enabled"
}
EOF
exit 0
