---
description: Audit codebase for greenfield cruft violations
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: [path]
---

# Greenfield Cruft Audit

Invoke the Cruft Auditor to scan for backwards-compatibility patterns.

**Target**: $ARGUMENTS (default: entire codebase)

Spawn the cruft-auditor agent to:
1. Scan for deprecation markers, backwards-compat code, and migration artifacts
2. Report violations with file/line references
3. Recommend cleanup actions
