# Vibe Hacker

A Claude Code plugin for hacking, development workflows, and greenfield projects.

## Features

### Klaus - Embedded Quality Auditor

Klaus is a pedantic embedded systems expert who audits your code for quality issues. Invoke him after major changes or to review unfamiliar codebases.

**Audit types:**
- `memory` - RAM, stack, globals, allocation patterns
- `timing` - ISRs, blocking calls, timeouts, real-time concerns
- `safety` - Error handling, defensive coding, robustness
- `style` - Code organization, naming, documentation
- `full` - Comprehensive audit (all of the above)

```bash
/klaus memory    # Check for memory issues
/klaus full      # Full codebase audit
```

Klaus checks for common embedded anti-patterns:
- Dynamic allocation (`malloc` on embedded)
- Floating point on 8-bit MCUs
- Fat ISRs (should set flag and exit)
- Unbounded busy-waits
- Missing timeouts on blocking calls

### Librodotus - Documentation Quality Auditor

Librodotus is a scholarly documentation purist who ensures your docs are useful, scannable, and accurate. Named after Herodotus—but unlike his namesake, he never embellishes.

**Audit types:**
- `readme` - README scannability, 30-second test
- `code` - Source code comments, API documentation
- `architecture` - System docs, decision records
- `freshness` - Staleness check, outdated references
- `full` - Comprehensive audit (all of the above)

```bash
/librodotus readme    # Audit README quality
/librodotus full      # Full documentation audit
```

Librodotus philosophy:
- "A README should answer 'what is this?' in 10 seconds."
- "The best comment explains *why*, not *what*."
- "Tables are your friend. Walls of text are your enemy."

### Shawn - Educational Mentor

Shawn is a warm mentor who views projects through an educator's lens. He asks: "What makes this teachable? How can we spark curiosity while building competence?"

**Review types:**
- `onboarding` - First five minutes, setup friction, initial success
- `concepts` - Clarity, progression, mental models
- `examples` - Quality, runnability, scaffolding
- `depth` - Challenge gradient, growth pathways
- `full` - Comprehensive educational review

```bash
/shawn onboarding   # How's the first experience?
/shawn full         # Full educational review
```

Shawn's approach:
- "Can someone see themselves succeeding here?"
- "What's the first 'aha!' moment, and how quickly can we get there?"
- "Is the complexity essential, or accidental?"

### Context Priming

Automatically prime Claude with project context on session start and after compaction.

- **SessionStart hook**: Full priming on session start and after compaction
- **/prime command**: Manual full priming when needed

### Greenfield Mode

Optional mode that prevents backwards-compatibility cruft in prototype/unreleased projects. Enable per-project via config.

When enabled:
- **PostToolUse hook**: Warns when edited files contain legacy patterns
- **Stop hook**: Reminds about greenfield rules at session end

Detected patterns:
- Deprecation comments (`// deprecated`, `@deprecated`, `# legacy`)
- Backwards-compatibility shims and re-exports
- Migration documentation ("the old way")
- Unused variable renaming (`_unused` prefix)

### Protected Paths

Control access to files and directories with a three-tier protection system:

| Tier | Behavior | Use Case |
|------|----------|----------|
| `readonly` | Blocks edits completely | Archived documents, historical records |
| `guided` | Blocks with skill suggestion | Planning docs that need managed workflow |
| `remind` | Warns but allows edit | Templates, config files |

Configure protection rules in `vibe-hacker.json`:

```json
{
  "protected_paths": {
    "rules": [
      {
        "pattern": "docs/archive/**",
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

**Pattern syntax**: Standard glob patterns (`*`, `**`, `?`, `[abc]`).

### Planning Skill

Manage planning documents (ADRs, FDPs, Action Plans) with proper numbering and lifecycle.

**Document types**:

| Type | Purpose | Example |
|------|---------|---------|
| ADR | Architecture Decision Record | `001-use-postgresql.md` |
| FDP | Feature Design Proposal | `FDP-001-auth-system.md` |
| AP | Action Plan | `AP-001-implement-login.md` |

**Creating documents** (auto-numbered):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py adr "Use PostgreSQL"
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py fdp "User Authentication"
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/new.py ap "Implement login"
```

**Listing documents**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py              # All active
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py --type adr   # Only ADRs
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/list.py --status proposed
```

**Archiving completed documents**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/archive.py ADR-001
```

The planning root is configurable via `protected_paths.planning_root` (default: `docs/planning`).

See [skills/planning/SKILL.md](skills/planning/SKILL.md) for full documentation.

### Configuration

All plugin settings are configured via `.claude/vibe-hacker.json`:

```json
{
  "greenfield_mode": true,
  "priming": {
    "files": ["README.md", "docs/ARCHITECTURE.md"],
    "globs": ["docs/planning/action-plans/*.md"],
    "instructions": "Focus on active work in progress."
  },
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [
      {"pattern": "docs/planning/*/archive/**", "tier": "readonly"},
      {"pattern": "docs/planning/**/*.md", "tier": "guided", "skill": "planning"}
    ]
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `greenfield_mode` | boolean | `false` | Enable greenfield mode checks |
| `priming.files` | string[] | `[]` | Files to load during priming |
| `priming.globs` | string[] | `[]` | Glob patterns for additional files |
| `priming.instructions` | string | `""` | Custom instructions shown during priming |
| `protected_paths.planning_root` | string | `"docs/planning"` | Root directory for planning documents |
| `protected_paths.rules` | array | `[]` | Protection rules (see Protected Paths section) |

## Requirements

- [jq](https://jqlang.github.io/jq/) - JSON processor (used by priming and greenfield scripts)

## Installation

### Via Local Marketplace (Development)

1. Create a marketplace directory with this plugin:
   ```bash
   mkdir -p my-marketplace/.claude-plugin
   echo '{"name": "my-marketplace", "plugins": [{"name": "vibe-hacker", "source": "../vibe-hacker"}]}' > my-marketplace/.claude-plugin/marketplace.json
   ```

2. In Claude Code:
   ```
   /plugin marketplace add ./my-marketplace
   /plugin install vibe-hacker@my-marketplace
   ```

3. Restart Claude Code

### Via GitHub Marketplace

Coming soon.

## Project Setup

After installing the plugin, configure your project:

1. **Create vibe-hacker.json** (copy from `templates/vibe-hacker.json.example`):
   ```bash
   cp /path/to/vibe-hacker/templates/vibe-hacker.json.example .claude/vibe-hacker.json
   # Edit to configure priming files and greenfield mode
   ```

2. **Create CLAUDE.md** (optional, copy from `templates/CLAUDE.md.example`):
   ```bash
   cp /path/to/vibe-hacker/templates/CLAUDE.md.example .claude/CLAUDE.md
   # Add project-specific guidelines
   ```

## Plugin Structure

```
vibe-hacker/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── agents/
│   ├── klaus.md            # Embedded quality auditor
│   ├── librodotus.md       # Documentation quality auditor
│   └── shawn.md            # Educational mentor
├── commands/
│   ├── klaus.md            # /klaus command
│   ├── librodotus.md       # /librodotus command
│   ├── prime.md            # /prime command
│   └── shawn.md            # /shawn command
├── hooks/
│   └── hooks.json          # Hook configuration
├── scripts/
│   ├── check-legacy-cruft.sh       # Legacy pattern detector
│   ├── check-protected-paths.sh    # Protected paths enforcer
│   ├── greenfield-stop-hook.sh     # Greenfield stop hook
│   └── prime.sh                    # Priming script
├── skills/
│   └── planning/
│       ├── SKILL.md                # Planning skill documentation
│       ├── scripts/
│       │   ├── new.py              # Create new planning docs
│       │   ├── archive.py          # Archive completed docs
│       │   ├── list.py             # List planning docs
│       │   └── config.py           # Shared configuration
│       └── templates/
│           ├── adr.md              # ADR template
│           ├── fdp.md              # FDP template
│           └── action-plan.md      # Action plan template
├── templates/
│   ├── CLAUDE.md.example           # Project guidelines template
│   └── vibe-hacker.json.example    # Plugin config template
└── docs/
    ├── ARCHITECTURE.md
    └── planning/
        ├── action-plans/
        ├── decision-records/
        └── feature-designs/
```

## Commands

| Command | Description |
|---------|-------------|
| `/prime` | Load full project context from vibe-hacker.json |
| `/klaus [type]` | Embedded quality audit (memory\|timing\|safety\|style\|full) |
| `/librodotus [type]` | Documentation audit (readme\|code\|architecture\|freshness\|full) |
| `/shawn [type]` | Educational review (onboarding\|concepts\|examples\|depth\|full) |

## Agents

| Agent | Description |
|-------|-------------|
| `klaus` | Pedantic embedded quality auditor |
| `librodotus` | Scholarly documentation quality auditor |
| `shawn` | Warm educational mentor focused on learnability |

## Hooks

| Event | Type | Behavior |
|-------|------|----------|
| SessionStart | command | Full priming (on start and after compaction) |
| PreToolUse (Edit\|Write) | command | Protected paths enforcement |
| PostToolUse (Edit\|Write) | command | Legacy cruft warning (if greenfield enabled) |
| Stop | command | Greenfield reminder (if greenfield enabled) |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Plugin design and components
- [Planning Skill](skills/planning/SKILL.md) - Managing planning documents
- [Planning Documents](docs/planning/) - Decision records, feature designs, action plans

## License

MIT

## Author

Michael Skiles (mike@mskiles.com)
