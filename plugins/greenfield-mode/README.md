# Greenfield Mode

A Claude Code plugin that prevents backwards-compatibility cruft in prototype projects.

## The Problem

When working on new projects, Claude tends to add backwards-compatibility code even when there are no users:

- Deprecation comments (`// deprecated: use newMethod()`)
- Re-exports for compatibility
- Documenting "the old way"
- Keeping old implementations "for reference"

This cruft creates confusion in greenfield projects where there is no "old way."

## What It Does

1. **Status Display** (SessionStart): Shows greenfield mode status and injects greenfield context into Claude
2. **Cruft Detection** (PostToolUse): Warns/blocks when edited files contain legacy patterns

## Installation

```bash
/plugin marketplace add /path/to/vibe-hacker
/plugin install greenfield-mode@vibe-hacker
```

## Configuration

Create `.claude/vibe-hacker.json` in your project:

```json
{
  "greenfield_mode": true
}
```

### Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `greenfield_mode` | boolean | `false` | Enable greenfield mode |
| `greenfield_strict` | boolean | `false` | Block edits (instead of warn) when cruft detected |
| `greenfield_patterns` | string[] | (built-in) | Custom patterns to detect (replaces defaults) |
| `greenfield_exclude` | string[] | `*.json`, `*.yaml`, `*.yml` | File globs to skip (merged with defaults) |

### Strict Mode

By default, greenfield-mode warns but allows edits when cruft is detected. Enable strict mode to block edits:

```json
{
  "greenfield_mode": true,
  "greenfield_strict": true
}
```

### Custom Patterns

Override the default cruft patterns:

```json
{
  "greenfield_mode": true,
  "greenfield_patterns": [
    "deprecated",
    "legacy",
    "TODO.*remove",
    "@deprecated"
  ]
}
```

## Default Patterns

The following patterns are detected by default (case-insensitive):

- `deprecated`, `legacy`, `obsolete`
- `backwards.compat`, `backward.compat`, `for compatibility`
- `TODO:.*remove.*migrat`, `TODO:.*remove.*later`, `FIXME:.*compat`
- `temporary.*shim`, `_unused`, `re-export`

## Hooks

| Event | Behavior |
|-------|----------|
| SessionStart | Display greenfield mode status, inject greenfield context |
| PostToolUse (Edit/Write) | Check edited file for cruft patterns |

## Requirements

- [jq](https://jqlang.github.io/jq/) - JSON processor

## Part of Vibe Hacker

This plugin is part of the [vibe-hacker](https://github.com/mjrskiles/vibe-hacker) plugin collection:

- **greenfield-mode** (this plugin) - Cruft prevention for prototypes
- **primer** - Context priming
- **planning** - ADRs, FDPs, Action Plans, Reports, Roadmap
- **expert-agents** - Code auditors, build/test/arch/size agents
- **backlog** - Lightweight project backlogs
- **briefcase** - Personal thought management

## License

MIT
