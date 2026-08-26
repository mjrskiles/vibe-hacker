# Roadmap

> Last updated: 2026-08-26

## Current State

Vibe Hacker is a working collection of 4 Claude Code plugins — greenfield-mode, primer,
librarian, backlog — used daily in active development. All are functional and stable.

`expert-agents` and `briefcase` were split out into the `sbl-cc-plugins` and `briefcase`
repos; the `planning` plugin was renamed `librarian`.

## Near Term

- [ ] Protected paths are bypassed by Bash-mediated writes (`sed -i`, `>`, `tee`) — the
      PreToolUse matcher only covers `Edit|Write`. Needs a design decision, not a patch.
- [ ] Public release preparation (clean up examples, test install flow)
- [ ] First-time setup experience (project wizard — see FDP-004)

## Long Term

- [ ] Public plugin marketplace listing
- [ ] Community contributions and feedback

## Recently Completed

- [x] Hook and doc defect sweep — prime.sh double-encoding, `**` glob expansion in both
      pattern matchers, cruft-checker self-exclusion, hook timeout units, stale docs
- [x] Backlog plugin — lightweight project backlogs
- [x] Multi-plugin architecture split (FDP-003, AP-001) — monolithic plugin → independent plugins
- [x] Planning v2 (FDP-005, AP-002) — YAML frontmatter, addenda, supersede, relate, migrations
- [x] Protected paths system (FDP-002) — readonly/guided/remind tiers
- [x] Context priming with focuses and haiku mode
- [x] Greenfield cruft detection and session review
