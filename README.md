# Firmware Hacker

A Claude Code plugin for firmware hacking, embedded development, and greenfield project workflows.

## Features

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
├── commands/
│   └── prime.md            # /prime slash command
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
