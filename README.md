# Firmware Hacker

A Claude Code plugin for firmware hacking, embedded development, and greenfield project workflows.

## Features

### Klaus - Firmware Quality Auditor

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

- **SessionStart hook**: Light priming shows available files
- **PreCompact hook**: Reminds to re-prime after context compaction
- **/prime command**: Full priming loads all configured files

Projects configure priming via `.claude/prime.json`:

```json
{
  "files": ["README.md", "docs/ARCHITECTURE.md"],
  "globs": ["docs/planning/action-plans/*.md"],
  "instructions": "Focus on active work in progress."
}
```

### Greenfield Mode

Prevents backwards-compatibility cruft in prototype/unreleased projects.

- **PostToolUse hook**: Warns when edited files contain legacy patterns
- **Stop hook**: Haiku reviews session for greenfield violations

Detected patterns:
- Deprecation comments (`// deprecated`, `@deprecated`, `# legacy`)
- Backwards-compatibility shims and re-exports
- Migration documentation ("the old way")
- Unused variable renaming (`_unused` prefix)

## Installation

### Via Local Marketplace (Development)

1. Create a marketplace directory with this plugin:
   ```bash
   mkdir -p my-marketplace/.claude-plugin
   echo '{"name": "my-marketplace", "plugins": [{"name": "firmware-hacker", "source": "../firmware-hacker"}]}' > my-marketplace/.claude-plugin/marketplace.json
   ```

2. In Claude Code:
   ```
   /plugin marketplace add ./my-marketplace
   /plugin install firmware-hacker@my-marketplace
   ```

3. Restart Claude Code

### Via GitHub Marketplace

Coming soon.

## Project Setup

After installing the plugin, configure your project:

1. **Create prime.json** (copy from `templates/prime.json.example`):
   ```bash
   cp /path/to/firmware-hacker/templates/prime.json.example .claude/prime.json
   # Edit to list your project's key files
   ```

2. **Create CLAUDE.md** (optional, copy from `templates/CLAUDE.md.example`):
   ```bash
   cp /path/to/firmware-hacker/templates/CLAUDE.md.example .claude/CLAUDE.md
   # Add project-specific guidelines
   ```

## Plugin Structure

```
firmware-hacker/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── agents/
│   ├── klaus.md            # Firmware quality auditor
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
│   ├── check-legacy-cruft.sh   # Legacy pattern detector
│   └── prime.sh                # Priming script
├── templates/
│   ├── CLAUDE.md.example       # Greenfield guidelines template
│   └── prime.json.example      # Priming config template
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
| `/prime` | Load full project context from prime.json |
| `/klaus [type]` | Firmware quality audit (memory\|timing\|safety\|style\|full) |
| `/librodotus [type]` | Documentation audit (readme\|code\|architecture\|freshness\|full) |
| `/shawn [type]` | Educational review (onboarding\|concepts\|examples\|depth\|full) |

## Agents

| Agent | Description |
|-------|-------------|
| `klaus` | Pedantic embedded firmware quality auditor |
| `librodotus` | Scholarly documentation quality auditor |
| `shawn` | Warm educational mentor focused on learnability |

## Hooks

| Event | Type | Behavior |
|-------|------|----------|
| SessionStart | command | Light priming (file list) |
| PreCompact | command | Re-prime reminder |
| PostToolUse (Edit\|Write) | command | Legacy cruft warning |
| Stop | prompt (Haiku) | Greenfield violation review |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Plugin design and components
- [Planning](docs/planning/) - Decision records, feature designs, action plans

## License

MIT

## Author

Michael Skiles (mike@mskiles.com)
