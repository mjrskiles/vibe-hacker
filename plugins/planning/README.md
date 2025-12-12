# Planning

A Claude Code plugin for structured planning documents with protected paths.

## Features

### Planning Documents

Manage ADRs, FDPs, Action Plans, and Roadmaps with proper numbering and lifecycle.

| Type | Purpose | Example |
|------|---------|---------|
| ADR | Architecture Decision Record | `ADR-001-use-postgresql.md` |
| FDP | Feature Design Proposal | `FDP-001-auth-system.md` |
| AP | Action Plan | `AP-001-implement-login.md` |
| Roadmap | Project goals (immediate/medium/long term) | `roadmap.md` |

**Creating documents** (auto-numbered):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py adr "Use PostgreSQL"
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py fdp "User Authentication"
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py ap "Implement login"
```

**Initialize roadmap**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/init-roadmap.py
```

**Updating status**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/update-status.py ADR-001 accepted
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/update-status.py FDP-001 "in progress"
```

**Listing documents**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py --type adr
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py --status proposed
```

**Archiving completed documents**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/archive.py ADR-001
```

### Protected Paths

Control access to files with three protection tiers:

| Tier | Behavior | Use Case |
|------|----------|----------|
| `readonly` | Blocks edits completely | Archives, historical records |
| `guided` | Blocks with skill suggestion | Planning docs |
| `remind` | Warns but allows edit | Templates, configs |

### Roadmap Reminder

PreCompact hook reminds you to update the roadmap before context compaction.

## Installation

```bash
/plugin marketplace add /path/to/vibe-hacker
/plugin install planning@vibe-hacker
```

## Configuration

Create `.claude/vibe-hacker.json` in your project:

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
    "planning_root": "docs/planning",
    "rules": [
      {
        "pattern": "docs/planning/*/archive/**",
        "tier": "readonly",
        "message": "Archives are read-only."
      },
      {
        "pattern": "docs/planning/**/*.md",
        "tier": "guided",
        "skill": "planning",
        "message": "Use the planning skill to manage these."
      }
    ]
  }
}
```

### Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `planning.subdirs.adr` | string | `"decision-records"` | Subdirectory for ADRs |
| `planning.subdirs.fdp` | string | `"feature-designs"` | Subdirectory for FDPs |
| `planning.subdirs.ap` | string | `"action-plans"` | Subdirectory for Action Plans |
| `protected_paths.planning_root` | string | `"docs/planning"` | Root for planning docs |
| `protected_paths.rules` | array | `[]` | Protection rules |

## Hooks

| Event | Behavior |
|-------|----------|
| PreCompact | Remind to update roadmap |
| PreToolUse (Edit/Write) | Check protected paths |

## Requirements

- [jq](https://jqlang.github.io/jq/) - JSON processor
- Python 3.x - For planning scripts

## Part of Vibe Hacker

This plugin is part of the [vibe-hacker](https://github.com/mjrskiles/vibe-hacker) plugin collection:

- **greenfield-mode** - Cruft prevention for prototypes
- **primer** - Context priming
- **planning** (this plugin) - ADRs, FDPs, Action Plans, Roadmap
- **expert-agents** - Klaus, Librodotus, Shawn

## License

MIT
