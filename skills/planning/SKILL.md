---
name: planning
description: Manage planning documents (ADRs, FDPs, action plans). Use when creating, archiving, or listing planning docs. Enforces proper numbering and structure.
allowed-tools: Read, Write, Bash, Glob, Grep
---

# Planning Skill

Manage planning documents with proper structure, numbering, and lifecycle.

## Document Types

| Type | Purpose | Naming |
|------|---------|--------|
| ADR | Architecture Decision Record - captures a decision and its context | `NNN-slug.md` |
| FDP | Feature Design Proposal - designs a feature before implementation | `FDP-NNN-slug.md` |
| AP | Action Plan - tracks implementation steps for a task | `AP-NNN-slug.md` |

## Configuration

The planning root directory is configurable in `vibe-hacker.json`:

```json
{
  "protected_paths": {
    "planning_root": "docs/planning"
  }
}
```

Default locations (relative to planning_root):
- ADRs: `decision-records/`
- FDPs: `feature-designs/`
- Action Plans: `action-plans/`

## When to Use This Skill

Use the planning scripts when:
- Creating a new planning document (ensures proper numbering)
- Archiving a completed or superseded document
- Listing active planning documents
- Checking document status

**Do NOT manually create or renumber planning documents.** Always use the scripts.

## Available Scripts

All scripts are in `${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/`.

### Create New Document

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py <type> "<title>"
```

Examples:
```bash
python3 scripts/new.py adr "Use PostgreSQL for persistence"
# Creates: <planning_root>/decision-records/004-use-postgresql-for-persistence.md

python3 scripts/new.py fdp "User Authentication System"
# Creates: <planning_root>/feature-designs/FDP-003-user-authentication-system.md

python3 scripts/new.py ap "Implement login flow"
# Creates: <planning_root>/action-plans/AP-001-implement-login-flow.md
```

### Archive Document

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/archive.py <doc-id>
```

Examples:
```bash
python3 scripts/archive.py ADR-001
# Moves to archive/, updates status to "Archived"

python3 scripts/archive.py FDP-002
# Moves to archive/, updates status to "Archived"
```

### List Documents

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py [--type TYPE] [--status STATUS]
```

Examples:
```bash
python3 scripts/list.py
# Lists all active planning documents

python3 scripts/list.py --type adr
# Lists only ADRs

python3 scripts/list.py --status proposed
# Lists documents with "Proposed" status
```

## Document Lifecycle

### ADR Lifecycle
```
Proposed → Accepted → [Superseded by ADR-NNN | Deprecated]
```

- **Proposed**: Under discussion, can be edited
- **Accepted**: Decision made, becomes read-only
- **Superseded**: Replaced by newer ADR, archived
- **Deprecated**: No longer applicable, archived

### FDP Lifecycle
```
Proposed → In Progress → [Implemented | Abandoned]
```

- **Proposed**: Design under review
- **In Progress**: Actively being implemented
- **Implemented**: Complete, archived
- **Abandoned**: Not pursued, archived

### Action Plan Lifecycle
```
Active → [Completed | Abandoned]
```

- **Active**: Work in progress
- **Completed**: All tasks done, archived
- **Abandoned**: Work stopped, archived

## Protected Paths

Planning documents may be protected by the PreToolUse hook:
- **Archived documents**: Read-only, cannot be edited
- **Accepted ADRs**: Read-only, create new ADR to supersede
- **Active documents**: May require using this skill to edit

If an edit is blocked, use the appropriate script to make changes.

## Templates

Templates are in `${CLAUDE_PLUGIN_ROOT}/skills/planning/templates/`:
- `adr.md` - Architecture Decision Record
- `fdp.md` - Feature Design Proposal
- `action-plan.md` - Action Plan

The `new.py` script automatically uses the correct template.
