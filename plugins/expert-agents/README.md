# Expert Agents

A Claude Code plugin with domain-specific code auditors.

## Agents

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

Librodotus is a scholarly documentation purist who ensures your docs are useful, scannable, and accurate. Named after Herodotus--but unlike his namesake, he never embellishes.

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

## Installation

```bash
/plugin marketplace add /path/to/vibe-hacker
/plugin install expert-agents@vibe-hacker
```

## Commands

| Command | Description |
|---------|-------------|
| `/klaus [type]` | Embedded quality audit (memory\|timing\|safety\|style\|full) |
| `/librodotus [type]` | Documentation audit (readme\|code\|architecture\|freshness\|full) |
| `/shawn [type]` | Educational review (onboarding\|concepts\|examples\|depth\|full) |

## No Configuration Needed

Expert agents are stateless and work out of the box. No configuration required.

## Part of Vibe Hacker

This plugin is part of the [vibe-hacker](https://github.com/mjrskiles/vibe-hacker) plugin collection:

- **greenfield-mode** - Cruft prevention for prototypes
- **primer** - Context priming
- **planning** - ADRs, FDPs, Action Plans, Reports, Roadmap
- **expert-agents** (this plugin) - Klaus, Librodotus, Shawn

## License

MIT
