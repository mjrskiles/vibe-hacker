---
description: Prime context with project files (use after session start or compaction)
allowed-tools: Read, Glob, Grep
---

# Context Priming

Loading project context based on priming configuration...

!${CLAUDE_PLUGIN_ROOT}/scripts/prime.sh --full

---

## After Priming

1. **Acknowledge** the files loaded and summarize key architectural points
2. **Identify** any active work in progress (check action plans, TODOs, recent commits)
3. **Note** the project's current state and any pending decisions
4. **Ask** clarifying questions if needed

If this is a fresh session, greet the user and offer to continue where they left off.
If this follows context compaction, acknowledge that context was restored.

$ARGUMENTS
