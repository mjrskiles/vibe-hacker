---
type: fdp
id: FDP-003
status: completed (2025-12-12)
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# FDP-003: Split into Multi-Plugin Architecture

## Status

Completed (2025-12-12)

## Summary

Split vibe-hacker into multiple focused plugins: a tiny universal `greenfield` plugin, a `planning` plugin for document workflows, and optionally an `expert-agents` plugin for domain-specific auditors.

## Motivation

The current monolithic vibe-hacker plugin bundles several independent features:

1. **Greenfield mode** - Universal, useful for any prototype project
2. **Context priming** - Generally useful, but tied to config
3. **Planning skill** - Opinionated ADR/FDP/AP workflow, not for everyone
4. **Protected paths** - Useful but coupled to planning
5. **Expert agents** - Domain-specific (embedded, docs, education)

Problems with the monolith:
- Users who want greenfield mode get planning baggage they don't need
- Users who want planning get embedded-focused agents they don't use
- Harder to explain: "What does vibe-hacker do?" has a long answer
- Feature creep risk as more things get added

## Detailed Design

### Overview

Split into 2-3 plugins with clear boundaries:

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    greenfield    │  │     planning     │  │  expert-agents   │
│                  │  │                  │  │    (optional)    │
│ - Cruft detection│  │ - ADR/FDP/AP/    │  │                  │
│ - Stop hook      │  │   Roadmap        │  │ - Klaus          │
│ - Basic priming  │  │ - Protected paths│  │ - Librodotus     │
│                  │  │ - Full priming   │  │ - Shawn          │
│ ~50 lines config │  │ - Planning skill │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ▲                     ▲                     ▲
        │                     │                     │
        └──────────┬──────────┴──────────┬─────────┘
                   │                     │
            .claude/vibe-hacker.json (shared config)
```

### Plugin 1: `greenfield`

**Purpose**: Prevent backwards-compatibility cruft in prototype projects.

**Features**:
- PostToolUse hook: Detect legacy patterns in edited files
- Stop hook: Haiku review for greenfield violations
- Basic priming: Load README.md and CLAUDE.md on session start

**Config** (minimal):
```json
{
  "greenfield_mode": true,
  "greenfield_patterns": ["// deprecated", "// legacy"]
}
```

**Size**: ~5 files, <500 lines total

### Plugin 2: `planning`

**Purpose**: Structured planning document workflows.

**Features**:
- Planning skill: ADRs, FDPs, Action Plans, Roadmap
- Protected paths: Tiered file access control
- Full priming: Configurable file/glob loading
- PreCompact hook: Roadmap update reminder

**Config**:
```json
{
  "priming": {
    "files": ["README.md"],
    "globs": ["docs/planning/**/*.md"]
  },
  "planning": {
    "subdirs": { "adr": "decisions", "fdp": "designs", "ap": "actions" }
  },
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [...]
  }
}
```

### Plugin 3: `expert-agents` (optional, could stay bundled)

**Purpose**: Domain-specific code auditors.

**Features**:
- Klaus: Embedded firmware auditor
- Librodotus: Documentation auditor
- Shawn: Educational review

**Config**: None needed (agents are self-contained)

### Shared Configuration

**Key question**: Can multiple plugins share one config file?

**Recommendation**: Yes, use `.claude/vibe-hacker.json` as a shared config.

Each plugin reads only its relevant keys:
- `greenfield` reads: `greenfield_mode`, `greenfield_patterns`
- `planning` reads: `priming`, `planning`, `protected_paths`
- `expert-agents` reads: nothing (stateless)

**Benefits**:
- Single file to manage
- Users installing multiple plugins don't duplicate config
- Familiar location for existing users

**Implementation**:
```python
# Each plugin's config.py
def load_config():
    # All plugins look in same location
    config_path = get_project_dir() / '.claude' / 'vibe-hacker.json'
    ...
```

### Alternative: Per-Plugin Config

Each plugin could have its own config:
- `.claude/greenfield.json`
- `.claude/planning.json`

**Rejected because**:
- More files to manage
- Confusing if user installs multiple
- Breaks existing setups

## File Changes

### New Repositories

| Repository | Description |
|------------|-------------|
| `greenfield` | Standalone greenfield mode plugin |
| `planning` | Planning documents + protected paths |
| `expert-agents` | Klaus, Librodotus, Shawn (or keep in vibe-hacker) |

### greenfield plugin structure

```
greenfield/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── check-legacy-cruft.sh
│   └── prime.sh (simplified)
├── commands/
│   └── prime.md (optional)
├── README.md
└── templates/
    └── greenfield.json.example
```

### planning plugin structure

```
planning/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── check-protected-paths.sh
│   ├── prime.sh (full version)
│   └── precompact-roadmap.sh
├── skills/
│   └── planning/
│       ├── SKILL.md
│       ├── scripts/*.py
│       └── templates/*.md
├── commands/
│   └── prime.md
├── README.md
└── templates/
    └── planning.json.example
```

## Implementation Phases

### Phase 1: Extract greenfield

1. Create `greenfield` repo with minimal cruft detection
2. Simplify prime.sh to basic README/CLAUDE.md loading
3. Test standalone functionality
4. Keep vibe-hacker working (no breaking changes yet)

### Phase 2: Extract planning

1. Create `planning` repo with full feature set
2. Move protected paths, priming (full), planning skill
3. Ensure shared config file works
4. Update documentation

### Phase 3: Deprecate vibe-hacker monolith

1. Update vibe-hacker README to point to new plugins
2. Keep expert-agents in vibe-hacker OR extract separately
3. Archive or maintain as meta-package that installs others

## Alternatives Considered

### Keep monolithic, use feature flags

Add `enabled: false` flags for each feature.

**Rejected**: Still installs everything, just hides it. Doesn't solve "what does this plugin do?" problem.

### Split into many micro-plugins

Separate plugins for: greenfield, priming, protected-paths, planning-skill, each agent.

**Rejected**: Too granular. Installation overhead. These features work together.

### Different config file per plugin

Each plugin owns `.claude/<plugin-name>.json`.

**Rejected**: User friction. Existing users would need to migrate. Related settings split across files.

## Decisions

1. **Naming**: `greenfield` - catchy, people will figure it out

2. **Expert agents**: Separate plugin, same repo (monorepo structure)

3. **Marketplace**: Release all at once, still in heavy dev mode

4. **Migration**: Not needed - we're greenfield, remember?

## References

- [ADR-001: Greenfield Mode](../decision-records/001-greenfield-mode.md)
- [ADR-002: Context Priming](../decision-records/002-context-priming.md)
- [Claude Code Plugins Reference](https://docs.anthropic.com/claude-code/plugins)

---

## Addenda
