#!/bin/bash
# stop-hook.sh
# Greenfield reminder at session end

set -euo pipefail

CONFIG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/vibe-hacker.json"

# Check if greenfield mode is enabled
if [[ -f "$CONFIG_FILE" ]]; then
    enabled=$(jq -r '.greenfield_mode // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
    if [[ "$enabled" == "true" ]]; then
        cat << 'EOF'
{
    "decision": "approve",
    "reason": "GREENFIELD: No backwards compatibility, no deprecation comments, delete unused code."
}
EOF
        exit 0
    fi
fi

# Greenfield mode not enabled
echo '{"decision": "approve", "reason": "Greenfield mode not enabled"}'
exit 0
