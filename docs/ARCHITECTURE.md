# Architecture

This document describes the architecture of the Vibe Hacker plugin for Claude Code.

## Overview

Vibe Hacker is a Claude Code plugin that provides four core capabilities:

1. **Context Priming** - Automatically load project context on session start
2. **Greenfield Mode** - Prevent backwards-compatibility cruft in prototype projects
3. **Protected Paths** - Control file access with tiered protection (readonly, guided, remind)
4. **Planning Skill** - Manage ADRs, FDPs, and Action Plans with proper lifecycle

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Claude Code                                 │
├──────────────────────────────────────────────────────────────────────┤
│  Hooks System                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │SessionStart │ │ PreToolUse  │ │ PostToolUse │ │    Stop     │     │
│  │   (prime)   │ │ (protect)   │ │(cruft check)│ │  (review)   │     │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘     │
│         │               │               │               │             │
│         ▼               ▼               ▼               ▼             │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    Vibe Hacker Plugin                       │      │
│  │  ┌──────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────┐ │      │
│  │  │ prime.sh │ │check-protected-│ │check-legacy- │ │Haiku │ │      │
│  │  │          │ │   paths.sh     │ │  cruft.sh    │ │Prompt│ │      │
│  │  └────┬─────┘ └───────┬────────┘ └──────┬───────┘ └──┬───┘ │      │
│  └───────┼───────────────┼─────────────────┼────────────┼─────┘      │
│          │               │                 │            │             │
│          ▼               ▼                 ▼            ▼             │
│  ┌─────────────┐ ┌─────────────┐   ┌─────────────┐ ┌──────────┐      │
│  │vibe-hacker  │ │   Config    │   │Edited Files │ │Transcript│      │
│  │   .json     │ │   Rules     │   │             │ │          │      │
│  └─────────────┘ └─────────────┘   └─────────────┘ └──────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

## Components

### Plugin Manifest

**Location**: `.claude-plugin/plugin.json`

Defines plugin metadata and references hook configuration:

```json
{
  "name": "vibe-hacker",
  "version": "0.1.0",
  "hooks": "./hooks/hooks.json"
}
```

### Hook Configuration

**Location**: `hooks/hooks.json`

Configures hooks:

| Hook | Matcher | Type | Script/Prompt |
|------|---------|------|---------------|
| SessionStart | (all) | command | `prime.sh --full` |
| SessionStart | compact | command | `prime.sh --full` (re-prime after compaction) |
| PreToolUse | Edit\|Write | command | `check-protected-paths.sh` |
| PostToolUse | Edit\|Write | command | `check-legacy-cruft.sh --warn-only` |
| Stop | (all) | prompt | Haiku greenfield review |

### Priming System

**Script**: `scripts/prime.sh`

**Purpose**: Load project context into Claude's working memory.

**Modes**:
- `--full`: Read and output file contents (default, used by SessionStart)
- `--light`: List available files without reading contents
- `--check`: Dry run showing what would be primed

**Fallback Chain**:
```
.claude/vibe-hacker.json  →  Configured files/globs
        ↓ (missing)
.claude/CLAUDE.md         →  Project guidelines
        ↓ (missing)
README.md                 →  Basic project info
        ↓ (missing)
docs/                     →  Scan for markdown files
```

**vibe-hacker.json priming Schema**:
```json
{
  "priming": {
    "files": ["path/to/file.md"],
    "globs": ["docs/**/*.md"],
    "instructions": "Custom priming instructions"
  }
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

### Protected Paths System

**Script**: `scripts/check-protected-paths.sh`

**Purpose**: Control file access with tiered protection rules.

**Protection Tiers**:

| Tier | Behavior | Exit Code | Use Case |
|------|----------|-----------|----------|
| `readonly` | Block edit completely | Non-zero with `permissionDecision: "deny"` | Archives, historical records |
| `guided` | Block with skill suggestion | Non-zero | Planning docs needing managed workflow |
| `remind` | Warn but allow edit | 0 | Templates, config files |

**Rule Matching**:
- Uses bash glob patterns (extended globbing with `**`)
- First matching rule wins
- No match = allow edit

**Configuration** (in `vibe-hacker.json`):
```json
{
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [
      {"pattern": "docs/planning/*/archive/**", "tier": "readonly", "message": "..."},
      {"pattern": "docs/planning/**/*.md", "tier": "guided", "skill": "planning", "message": "..."}
    ]
  }
}
```

### Planning Skill

**Location**: `skills/planning/`

**Purpose**: Manage planning documents (ADRs, FDPs, Action Plans) with proper numbering and lifecycle.

**Components**:
- `SKILL.md` - Skill documentation (auto-invoked when guided tier suggests it)
- `scripts/new.py` - Create new documents with auto-numbering
- `scripts/archive.py` - Move completed documents to archive
- `scripts/list.py` - List active documents with status
- `scripts/config.py` - Shared configuration utilities
- `templates/` - Document templates

**Document Lifecycle**:
```
ADR:  Proposed → Accepted → [Superseded | Deprecated]
FDP:  Proposed → In Progress → [Implemented | Abandoned]
AP:   Active → [Completed | Abandoned]
```

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
SessionStart hook (or compact matcher)
      │
      ▼
prime.sh --full
      │
      ├── Read .claude/vibe-hacker.json
      │   └── Load configured files and globs
      │
      └── (fallback chain if no config)
      │
      ▼
Output file contents to Claude context
```

### Code Editing
```
User requests edit
      │
      ▼
Claude uses Edit/Write tool
      │
      ▼
PreToolUse hook triggers
      │
      ▼
check-protected-paths.sh
      │
      ├── Parse JSON input for file_path
      ├── Load rules from vibe-hacker.json
      ├── Match against patterns
      │
      ▼
┌─────────────────────────────────────────────┐
│  readonly: Block (permissionDecision: deny) │
│  guided:   Block + show skill commands      │
│  remind:   Warn + allow (exit 0)            │
│  no match: Allow (exit 0)                   │
└─────────────────────────────────────────────┘
      │ (if allowed)
      ▼
PostToolUse hook triggers
      │
      ▼
check-legacy-cruft.sh
      │
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
