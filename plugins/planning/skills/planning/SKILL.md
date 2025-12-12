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
| Roadmap | Project goals and vision (immediate, medium, long term) | `roadmap.md` |

## Roadmap

The roadmap is a single markdown file tracking project goals at different time horizons:

- **Immediate** (This Week) - Current focus
- **Medium Term** (This Month) - Coming up next
- **Long Term** (This Quarter+) - Vision and direction
- **Recently Completed** - What was just finished

### Initialize Roadmap

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/init-roadmap.py
```

This creates `<planning_root>/roadmap.md` from the template.

### Keeping it Updated

A **PreCompact hook** reminds you to update the roadmap before context compaction:
1. Move completed items to "Recently Completed"
2. Update "Immediate" goals based on progress
3. Adjust priorities as needed
4. Update the "Last updated" date

The roadmap is human-editable and should be updated regularly to reflect project state.

## Configuration

Configure planning directories in `vibe-hacker.json`:

```json
{
  "planning": {
    "subdirs": {
      "adr": "decision-records",
      "fdp": "feature-designs",
      "ap": "action-plans"
    }
  },
  "protected_paths": {
    "planning_root": "docs/planning"
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `protected_paths.planning_root` | `docs/planning` | Root directory for all planning docs |
| `planning.subdirs.adr` | `decision-records` | Subdirectory for ADRs |
| `planning.subdirs.fdp` | `feature-designs` | Subdirectory for FDPs |
| `planning.subdirs.ap` | `action-plans` | Subdirectory for Action Plans |

With the defaults above, documents are created at:
- ADRs: `docs/planning/decision-records/NNN-slug.md`
- FDPs: `docs/planning/feature-designs/FDP-NNN-slug.md`
- Action Plans: `docs/planning/action-plans/AP-NNN-slug.md`

## When to Use This Skill

Use the planning scripts when:
- Creating a new planning document (ensures proper numbering)
- Updating a document's status (e.g., Proposed → Accepted)
- Editing a document (validates status allows editing)
- Archiving a completed or superseded document
- Listing active planning documents

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

### Update Status

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/update-status.py <doc-id> <new-status>
```

Examples:
```bash
python3 scripts/update-status.py ADR-001 accepted
# Updates ADR-001 status from Proposed to Accepted

python3 scripts/update-status.py FDP-002 "in progress"
# Updates FDP-002 status to In Progress

python3 scripts/update-status.py AP-001 completed
# Updates AP-001 status to Completed (suggests archiving)
```

Valid statuses by type:
- **ADR**: proposed, accepted, deprecated, superseded
- **FDP**: proposed, in progress, implemented, abandoned
- **AP**: active, completed, abandoned

### Check Edit Permission

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/edit.py <doc-id>
```

Checks if a document can be edited based on its status. Outputs the file path if editable.

Examples:
```bash
python3 scripts/edit.py ADR-001
# If Proposed: outputs path, exit 0
# If Accepted: outputs error, exit 1

python3 scripts/edit.py FDP-002 --force
# Force edit even if locked (outputs warning)

python3 scripts/edit.py AP-001 --quiet
# Only output path, no messages
```

**Locked statuses** (require `--force` to edit):
- **ADR**: accepted, deprecated, superseded
- **FDP**: implemented, abandoned
- **AP**: completed, abandoned

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

Planning documents are configured with protection rules in `vibe-hacker.json`:

- **Archived documents** (`readonly` tier): Cannot be edited
- **Active planning documents** (`remind` tier): Editable with a warning suggesting skill scripts

The `edit.py` script provides additional validation based on document status (e.g., accepted ADRs are locked).

## Templates

Templates are in `${CLAUDE_PLUGIN_ROOT}/skills/planning/templates/`:
- `adr.md` - Architecture Decision Record
- `fdp.md` - Feature Design Proposal
- `action-plan.md` - Action Plan
- `roadmap.md` - Project Roadmap

The `new.py` script automatically uses the correct template. Use `init-roadmap.py` to initialize the roadmap.
