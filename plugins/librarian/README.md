# Librarian

A Claude Code plugin for structured planning documents with protected paths.

## Features

### Planning Documents (v0.2.1)

Manage ADRs, FDPs, Action Plans, Reports, and Roadmaps with:
- YAML frontmatter for structured metadata
- Document relationships (supersedes, related)
- Append-only addenda for locked documents
- Automatic numbering and lifecycle management
- Archive index generation for decluttered directories

| Type | Purpose | ID Format | Default Dir |
|------|---------|-----------|-------------|
| ADR | Architecture Decision Record | `ADR-001` | `decisions/` |
| FDP | Feature Design Proposal | `FDP-001` | `designs/` |
| AP | Action Plan | `AP-001` | `action-plans/` |
| Report | Reports and analysis | `RPT-001` | `reports/` |
| Log | Dated entries, one file per thread | N/A | `logs/<thread>.md` |
| Roadmap | Project goals | N/A | `roadmap.md` |

### Basic Operations

**Creating documents** (auto-numbered with frontmatter):
```bash
python3 scripts/new.py adr "Use PostgreSQL"
python3 scripts/new.py fdp "User Authentication"
python3 scripts/new.py ap "Implement login"
python3 scripts/new.py report "Q4 Analysis"
```

**Updating status**:
```bash
python3 scripts/update-status.py ADR-001 accepted
python3 scripts/update-status.py FDP-001 "in progress"
python3 scripts/update-status.py RPT-001 published
```

**Listing documents**:
```bash
python3 scripts/list.py
python3 scripts/list.py --type adr
python3 scripts/list.py --type report
```

**Archiving completed documents** (generates ARCHIVE.md index):
```bash
python3 scripts/archive.py ADR-001
python3 scripts/archive.py FDP-002
python3 scripts/archive.py --regenerate-index  # rebuild index without archiving
```

### New in v0.2.1

**Add addenda to locked documents**:
```bash
python3 scripts/append.py ADR-001 "Performance Note" --body "Read replicas work well"
```

**Supersede a document**:
```bash
python3 scripts/supersede.py ADR-001 "Revised Database Strategy"
```

**Link related documents**:
```bash
python3 scripts/relate.py ADR-001 FDP-003 --bidirectional
```

### Logs, retired types, archive notes

**Add a dated entry to a thread's log** (`<planning_root>/logs/<thread>.md`, created on first use):
```bash
python3 scripts/log.py davis "Step 6 listening" --body "Build: main a5c4f3d ..."
```

**Retire a type**: list its key in `planning.retired`. Its documents stay readable and can still be
archived; `new.py` and `supersede.py` refuse to create one.

**Archive note**: `archive.py` leaves a note under an archived document's title with the date, the
status it had, and the sentence in `planning.archive_note`.

**Templates**: a template of the same name in `<planning_root>/templates/` takes precedence over the
shipped one.

**Review**: `review.py` lists open documents, then finished documents that are still live.

### Protected Paths

Control access to files with three protection tiers:

| Tier | Behavior | Use Case |
|------|----------|----------|
| `readonly` | Blocks edits completely | Archives, historical records |
| `guided` | Blocks with skill suggestion | Planning docs |
| `remind` | Warns but allows edit | Templates, configs |

### Roadmap Reminder

PreCompact hook reminds you to check the roadmap before context compaction — only when
the roadmap has been touched in the last 30 days (its `> Last updated:` line, falling back to git
history, then mtime).
A roadmap nobody maintains stops nagging on its own.

## Installation

```bash
/plugin marketplace add /path/to/vibe-hacker
/plugin install librarian@vibe-hacker
```

## Configuration

Create `.claude/vibe-hacker.json` in your project:

```json
{
  "planning": {
    "subdirs": {
      "adr": "decisions",
      "fdp": "designs",
      "ap": "action-plans",
      "report": "reports"
    },
    "retired": [],
    "archive_note": "A historical record."
  },
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [
      {
        "pattern": "docs/planning/*/archive/**",
        "tier": "readonly",
        "message": "Archives are read-only."
      },
      {
        "pattern": "docs/planning/**/*.md",
        "tier": "remind",
        "skill": "librarian",
        "message": "Use the librarian skill to manage these."
      }
    ]
  }
}
```

### Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `planning.subdirs.adr` | string | `"decisions"` | Subdirectory for ADRs |
| `planning.subdirs.fdp` | string | `"designs"` | Subdirectory for FDPs |
| `planning.subdirs.ap` | string | `"action-plans"` | Subdirectory for Action Plans |
| `planning.subdirs.report` | string | `"reports"` | Subdirectory for Reports |
| `planning.retired` | array | `[]` | Type keys that can no longer be created |
| `planning.archive_note` | string | `"A historical record."` | Closing sentence of the archive note |
| `protected_paths.planning_root` | string | `"docs/planning"` | Root for planning docs |
| `protected_paths.rules` | array | `[]` | Protection rules |

## Document Format

All documents use YAML frontmatter:

```yaml
---
type: adr
id: ADR-001
status: accepted
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: [FDP-003]
---

# ADR-001: Title

## Status
Accepted

...content...

---

## Addenda

### 2025-12-13: Clarification
Additional notes added after acceptance.
```

## Hooks

| Event | Behavior |
|-------|----------|
| PreCompact | Remind to update roadmap |
| PreToolUse (Edit/Write) | Check protected paths |

## Requirements

- [jq](https://jqlang.github.io/jq/) - JSON processor
- Python 3.10+ - For planning scripts
- PyYAML (optional) - For better YAML handling
- pytest - For the tests

## Tests

```bash
pytest plugins/librarian/tests
```

The tests run each script against a temporary project directory.

## Part of Vibe Hacker

This plugin is part of the [vibe-hacker](https://github.com/mjrskiles/vibe-hacker) plugin collection:

- **greenfield-mode** - Cruft prevention for prototypes
- **primer** - Context priming
- **librarian** (this plugin) - ADRs, FDPs, Action Plans, Reports, Roadmap
- **backlog** - Lightweight project backlogs
- **datasheet** - Page-cited lookups against local datasheets and manuals

## License

MIT
