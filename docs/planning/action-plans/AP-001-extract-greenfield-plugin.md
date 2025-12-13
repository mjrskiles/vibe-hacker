---
type: ap
id: AP-001
status: completed
created: 2025-12-12
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# AP-001: Extract Greenfield Plugin

## Status

Completed

## Created

2025-12-12

## Completed

2025-12-12

## Goal

Extract greenfield mode into a tiny, standalone plugin. This is Phase 1 of the multi-plugin split (FDP-003).

## Context

Greenfield mode is universally useful for any prototype project. It should be a minimal plugin that:
- Detects legacy/backwards-compat patterns in edited files
- Reviews session for greenfield violations (stop hook)
- Optionally does basic priming (README.md, CLAUDE.md)

## Tasks

### Setup monorepo structure

- [x] Create `plugins/` directory in vibe-hacker repo
- [x] Create `plugins/greenfield/` with plugin structure
- [x] Update root README to explain monorepo layout

### Extract greenfield plugin

- [x] Create `plugins/greenfield/.claude-plugin/plugin.json`
- [x] Create `plugins/greenfield/hooks/hooks.json` (PostToolUse, Stop)
- [x] Copy and simplify `check-legacy-cruft.sh` to greenfield plugin
- [x] Create minimal `prime.sh` (just README.md + CLAUDE.md fallback)
- [x] Create `plugins/greenfield/README.md`
- [x] Create `plugins/greenfield/templates/greenfield.json.example`

### Config handling

- [x] Greenfield reads from `.claude/vibe-hacker.json` (shared config)
- [x] Only reads `greenfield_mode` and `greenfield_patterns` keys
- [x] Works standalone (no dependency on other plugins)

### Testing

- [ ] Test greenfield plugin in isolation (fresh project)
- [ ] Verify cruft detection works
- [ ] Verify stop hook fires
- [ ] Test with and without config file (defaults work)

### Documentation

- [x] Update greenfield README with installation instructions
- [x] Document config options
- [x] Add to monorepo root README

## Notes

- Root plugin files deleted (clean break, greenfield project)
- All three plugins extracted: greenfield, planning, expert-agents
- Shared config via `.claude/vibe-hacker.json`

## Completion Criteria

- [x] `plugins/greenfield/` is a valid Claude Code plugin
- [ ] Can be installed standalone via marketplace (needs testing)
- [x] Detects legacy patterns in edited files
- [x] Stop hook reviews for violations
- [x] Works without any config (sensible defaults)
- [x] Works with shared vibe-hacker.json config

## References

- [FDP-003: Multi-Plugin Architecture](../feature-designs/FDP-003-split-into-multi-plugin-architecture.md)

---

## Addenda
