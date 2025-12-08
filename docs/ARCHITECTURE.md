# Architecture

This document describes the architecture of the Firmware Hacker plugin for Claude Code.

## Overview

Firmware Hacker is a Claude Code plugin that provides two core capabilities:

1. **Context Priming** - Automatically load project context on session start
2. **Greenfield Mode** - Prevent backwards-compatibility cruft in prototype projects

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code                              │
├─────────────────────────────────────────────────────────────┤
│  Hooks System                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │SessionStart │ │ PostToolUse │ │    Stop     │            │
│  │   (prime)   │ │(cruft check)│ │  (review)   │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Firmware Hacker Plugin                  │    │
│  │  ┌──────────┐  ┌──────────────────┐  ┌───────────┐  │    │
│  │  │ prime.sh │  │check-legacy-cruft│  │  Haiku    │  │    │
│  │  │          │  │      .sh         │  │  Prompt   │  │    │
│  │  └────┬─────┘  └────────┬─────────┘  └─────┬─────┘  │    │
│  └───────┼─────────────────┼──────────────────┼────────┘    │
│          │                 │                  │              │
│          ▼                 ▼                  ▼              │
│  ┌─────────────┐   ┌─────────────┐    ┌─────────────┐       │
│  │ prime.json  │   │Edited Files │    │ Transcript  │       │
│  │ (project)   │   │             │    │             │       │
│  └─────────────┘   └─────────────┘    └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Plugin Manifest

**Location**: `.claude-plugin/plugin.json`

Defines plugin metadata and references hook configuration:

```json
{
  "name": "firmware-hacker",
  "version": "0.1.0",
  "hooks": "./hooks/hooks.json"
}
```

### Hook Configuration

**Location**: `hooks/hooks.json`

Configures four hooks:

| Hook | Type | Script/Prompt |
|------|------|---------------|
| SessionStart | command | `prime.sh --light` |
| PreCompact | command | inline echo |
| PostToolUse | command | `check-legacy-cruft.sh --warn-only` |
| Stop | prompt | Haiku greenfield review |

### Priming System

**Script**: `scripts/prime.sh`

**Purpose**: Load project context into Claude's working memory.

**Modes**:
- `--light`: List available files (SessionStart)
- `--full`: Read and output file contents (/prime command)
- `--check`: Dry run showing what would be primed

**Fallback Chain**:
```
.claude/prime.json    →  Configured files/globs
        ↓ (missing)
.claude/CLAUDE.md     →  Project guidelines
        ↓ (missing)
README.md             →  Basic project info
        ↓ (missing)
docs/                 →  Scan for markdown files
```

**prime.json Schema**:
```json
{
  "files": ["path/to/file.md"],      // Explicit file paths
  "globs": ["docs/**/*.md"],          // Glob patterns
  "instructions": "Custom priming instructions"
}
```

### Legacy Cruft Detection

**Script**: `scripts/check-legacy-cruft.sh`

**Purpose**: Detect backwards-compatibility patterns that shouldn't exist in greenfield projects.

**Detected Patterns**:
- `// deprecated`, `# deprecated`, `@deprecated`
- `// legacy`, `// old:`, `// old way`
- `// TODO: remove after migration`
- `// backwards compat`, `// for compatibility`

**Modes**:
- Default: Exit 2 (block) on detection
- `--warn-only`: Exit 0 (warn) on detection

**Input Sources**:
- Hook stdin (JSON with `tool_input.file_path`)
- Command line arguments
- Git diff (uncommitted changes)

### Greenfield Review (Stop Hook)

**Type**: Prompt-based (Haiku LLM)

**Purpose**: Review Claude's work for greenfield violations before session ends.

**Violations Checked**:
- Deprecation comments
- Backwards-compatibility code
- Migration documentation
- Re-exports and unused variable renaming

**Response Format**:
```json
{
  "decision": "approve",
  "reason": "WARNING - GREENFIELD VIOLATION: [issue]"
}
```

## Data Flow

### Session Start
```
SessionStart hook
      │
      ▼
prime.sh --light
      │
      ├── Read .claude/prime.json
      │   └── List configured files
      │
      └── (fallback chain if no prime.json)
      │
      ▼
Output file list to Claude context
```

### Code Editing
```
User requests edit
      │
      ▼
Claude uses Edit/Write tool
      │
      ▼
PostToolUse hook triggers
      │
      ▼
check-legacy-cruft.sh
      │
      ├── Parse JSON input for file_path
      ├── Grep for legacy patterns
      │
      ▼
Warn if patterns found (exit 0)
```

### Session End
```
Claude finishes response
      │
      ▼
Stop hook triggers
      │
      ▼
Haiku reviews transcript
      │
      ├── Check for greenfield violations
      │
      ▼
Approve with warning if violations found
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_PLUGIN_ROOT` | Path to plugin directory (for hook scripts) |
| `CLAUDE_PROJECT_DIR` | Path to project using the plugin |

## Extending the Plugin

### Adding a New Hook

1. Add configuration to `hooks/hooks.json`
2. Create script in `scripts/` if command-based
3. Document in this file

### Adding a New Command

1. Create markdown file in `commands/`
2. Add frontmatter with description and allowed-tools
3. Document in README.md

### Modifying Detection Patterns

Edit `CRUFT_PATTERNS` array in `scripts/check-legacy-cruft.sh`.

## Design Decisions

See `docs/planning/decision-records/` for architectural decisions.

## References

- [Claude Code Hooks Guide](https://docs.anthropic.com/claude-code/hooks)
- [Claude Code Plugins Reference](https://docs.anthropic.com/claude-code/plugins)
