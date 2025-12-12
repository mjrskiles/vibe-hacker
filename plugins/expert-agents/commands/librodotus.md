---
description: Invoke Librodotus for documentation quality audit (readme|code|architecture|freshness|full)
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: [audit-type]
---

# Librodotus Documentation Audit Request

Invoke the Librodotus subagent to perform a documentation quality audit.

**Audit type requested**: $ARGUMENTS

If no audit type specified, ask the user what they'd like audited, or suggest a full audit for first-time reviews.

**Audit types available:**
- `readme` - README scannability, 30-second test, first impressions
- `code` - Source code comments, API docs, comment quality
- `architecture` - System docs, ARCHITECTURE.md, decision records
- `freshness` - Staleness check, outdated refs, broken links, working examples
- `full` - Comprehensive audit (all of the above)

**Current project context:**
!ls -la
!head -100 README.md 2>/dev/null || echo "No README found"
!ls -la docs/ 2>/dev/null || echo "No docs/ directory"

Spawn Librodotus to perform the requested audit. Librodotus should:
1. Review the documentation structure
2. Run the appropriate checklist(s)
3. Report findings with specific locations
4. Deliver a verdict

Remember: Librodotus values brevity, scannability, and unix-like usefulness. Documentation should serve readers, not writers.
