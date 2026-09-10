# Vibe Hacker

A collection of Claude Code plugins for hacking, development workflows, and greenfield projects.

## Plugins

| Plugin | Description | Use Case |
|--------|-------------|----------|
| [greenfield-mode](plugins/greenfield-mode/) | Prevent backwards-compatibility cruft | Prototype projects |
| [primer](plugins/primer/) | Context priming on session start | Any project |
| [librarian](plugins/librarian/) | ADRs, FDPs, Action Plans, Reports, Roadmap | Structured planning |
| [backlog](plugins/backlog/) | Lightweight project backlogs for ideas and polish items | Task tracking |
| [datasheet](plugins/datasheet/) | Page-cited lookups against local datasheets, reference manuals, errata — and curation of the catalog | Embedded / hardware |

## Quick Start

```bash
# Add the vibe-hacker directory as a marketplace
/plugin marketplace add /path/to/vibe-hacker

# Install individual plugins
/plugin install greenfield-mode@vibe-hacker
/plugin install primer@vibe-hacker
/plugin install librarian@vibe-hacker
/plugin install backlog@vibe-hacker
```

## Plugin Overview

### greenfield-mode

Prevents backwards-compatibility cruft in prototype projects.

**Hooks:**
- SessionStart: Show greenfield status
- PostToolUse: Detect legacy patterns in edited files

**Config:** `greenfield_mode`, `greenfield_strict`, `greenfield_patterns`, `greenfield_exclude`

[Full documentation](plugins/greenfield-mode/README.md)

### primer

Context priming - automatically load project files on session start.

**Hooks:**
- SessionStart: Load configured files
- After Compact: Reload files

**Config:** `priming.files`, `priming.globs`, `priming.instructions`

[Full documentation](plugins/primer/README.md)

### librarian

Structured planning documents with protected paths.

**Features:**
- ADRs, FDPs, Action Plans, Reports, Roadmap
- YAML frontmatter for structured metadata
- Append-only addenda for locked documents
- Document relationships (supersedes, related)
- Protected path enforcement (readonly/guided/remind tiers)

**Hooks:**
- PreCompact: Roadmap update reminder
- PreToolUse: Protected paths check

**Config:** `planning`, `protected_paths`

[Full documentation](plugins/librarian/README.md)

### backlog

Lightweight task tracking for ideas, polish items, and small improvements.

**Commands:**
- `/backlog add davis "Add velocity"` - Add an item
- `/backlog davis` - List items in a backlog
- `/backlog done davis 3` - Mark done
- `/backlog review davis` - Analyze and prioritize

**Config:** `backlog` (root directory)

[Full documentation](plugins/backlog/skills/backlog/SKILL.md)

### datasheet

Page-cited answers from a local corpus of datasheets, reference manuals,
errata sheets, and schematics. Stops the "plausible number, no source"
failure mode in embedded work: every fact carries document, revision,
section, and printed page; gaps are reported as "not stated" instead of
filled from memory; the errata sheet is always checked.

**Skill:** `datasheet` — in-context lookups, document-type routing (reference
manual vs datasheet vs errata), compare-against-code reports.

**Skill:** `curate-corpus` — the maintenance side: works through `shelf debt`
(unknown revisions, missing titles and bylines, unset page offsets, absent
source URLs) by pairing the `shelf` CLI, which enumerates and performs every
write, with a fan-out of curator agents, which read pages and propose values.
Agents never write, so a bad read is a rejected proposal rather than a
corrupted record.

**Agent:** `datasheet-reader` — deep reads across sections or documents,
driver/schematic audits, cataloguing new PDFs.

**Agent:** `corpus-curator` — settles the catalog fields for one document from
its own pages, and returns each value with the page it was read from.

**Corpus:** a [shelf](https://github.com/mjrskiles/shelf) — `<root>/shelf.json`
(tracked) catalogues the documents, `shelf search` / `grep` / `read` / `toc`
work the full-text index, and the PDFs stay local. Requires the `shelf` CLI
and poppler.

**Config:** `datasheet` (`root`, default `docs/reference`)

[Full documentation](plugins/datasheet/skills/datasheet/SKILL.md)

## Shared Configuration

All plugins read from `.claude/vibe-hacker.json`:

```json
{
  "greenfield_mode": true,
  "greenfield_strict": false,
  "greenfield_patterns": ["deprecated", "legacy", "@deprecated"],
  "priming": {
    "files": ["README.md"],
    "globs": ["docs/planning/action-plans/*.md"],
    "instructions": "Focus on active work."
  },
  "planning": {
    "subdirs": {
      "adr": "decisions",
      "fdp": "designs",
      "ap": "action-plans",
      "report": "reports"
    }
  },
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [
      {"pattern": "docs/planning/*/archive/**", "tier": "readonly"}
    ]
  }
}
```

Each plugin reads only its relevant keys:
- `greenfield-mode` reads: `greenfield_mode`, `greenfield_strict`, `greenfield_patterns`, `greenfield_exclude`
- `primer` reads: `priming`, `greenfield_mode` (for display)
- `librarian` reads: `planning`, `protected_paths`
- `backlog` reads: `backlog` (root directory)
- `datasheet` reads: `datasheet` (`root` — corpus directory, default `docs/reference`)

## Repository Structure

```
vibe-hacker/
├── plugins/
│   ├── greenfield-mode/      # Cruft prevention
│   ├── primer/               # Context priming
│   ├── librarian/            # Planning documents
│   ├── backlog/              # Project backlogs
│   └── datasheet/            # Corpus lookups and curation
├── docs/
│   └── planning/             # This project's planning docs
└── README.md
```

## Requirements

- [jq](https://jqlang.github.io/jq/) - JSON processor (greenfield-mode, primer, librarian)
- Python 3.x - librarian and backlog scripts
- [shelf](https://github.com/mjrskiles/shelf) + poppler - datasheet plugin

## License

MIT

## Author

Michael Skiles (michael@soundbytelabs.net)
