# ADR-002: Context Priming System

## Status

Accepted

## Date

2024-12-08

## Context

Claude Code sessions lose context in two scenarios:

1. **New session**: Starting fresh with no project knowledge
2. **Compaction**: Long sessions get compacted, losing earlier context

Users must manually re-explain project structure, conventions, and current work state. This is tedious and error-prone.

## Decision

Implement a layered priming system:

### Light Priming (SessionStart hook)

Automatically runs on session start. Outputs:
- List of files available for priming
- Custom instructions from prime.json
- Prompt to use `/prime` for full context

### Full Priming (/prime command)

User-invoked command that:
- Reads all files specified in prime.json
- Outputs full file contents to context
- Provides instructions for Claude to acknowledge and summarize

### Pre-Compaction Reminder (PreCompact hook)

Warns user before compaction that they should re-prime afterward.

### Fallback Chain

If prime.json is missing, gracefully degrade:
```
.claude/prime.json → .claude/CLAUDE.md → README.md → docs/
```

### Configuration Format

Projects configure priming via `.claude/prime.json`:
```json
{
  "files": ["explicit/paths.md"],
  "globs": ["docs/**/*.md"],
  "instructions": "Focus on active action plans"
}
```

## Consequences

**Benefits:**
- Consistent context across sessions
- Project-specific configuration
- Graceful degradation for unconfigured projects
- User control over when full priming occurs

**Costs:**
- Requires project setup (prime.json)
- Full priming consumes context window

**Trade-offs:**
- Light priming on SessionStart (not full) to avoid context bloat
- User must invoke /prime manually after compaction
- Glob support adds complexity but enables dynamic file discovery

## Alternatives Considered

### Full priming on SessionStart

Automatically load all files on every session start.

**Rejected**: Consumes too much context window. Light priming + manual /prime is more efficient.

### Hook-based full priming on compaction

Automatically re-prime after compaction.

**Rejected**: No post-compaction hook exists. PreCompact reminder is the best available option.

### Hardcoded file list

Always load README.md and docs/ARCHITECTURE.md.

**Rejected**: Not flexible enough. Projects have different structures.

## Open Questions

- Should there be a `/prime --light` variant for manual light priming?
- Should priming track which files were loaded to avoid duplicates?

## References

- [Claude Code Hooks Guide](https://docs.anthropic.com/claude-code/hooks)
- [Claude Code Commands](https://docs.anthropic.com/claude-code/commands)
