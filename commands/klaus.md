---
description: Invoke Klaus for firmware quality audit (memory|timing|safety|style|full)
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: [audit-type]
---

# Klaus Audit Request

Invoke the Klaus subagent to perform a firmware quality audit.

**Audit type requested**: $ARGUMENTS

If no audit type specified, ask the user what they'd like audited, or suggest a full audit for unfamiliar codebases.

**Audit types available:**
- `memory` - RAM, stack, globals, allocation patterns
- `timing` - ISRs, blocking calls, timeouts, real-time concerns
- `safety` - Error handling, defensive coding, robustness
- `style` - Code organization, naming, documentation
- `full` - Comprehensive audit (all of the above)

**Current project context:**
!ls -la
!head -50 README.md 2>/dev/null || echo "No README found"

Spawn Klaus to perform the requested audit. Klaus should:
1. Review the codebase structure
2. Run the appropriate checklist(s)
3. Report findings with specific file/line references
4. Deliver a verdict

Remember: Klaus is pedantic, direct, and resource-obsessed. He grudgingly approves only the cleanest code.
