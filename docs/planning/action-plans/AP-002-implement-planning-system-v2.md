---
type: ap
id: AP-002
status: active
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# AP-002: Implement Planning System v2

## Status

Active

## Created

2025-12-13

## Goal

Implement FDP-005: Planning System v2 with frontmatter, addenda, document relationships, extensible types, and the `vibe-doc` migration system. Test on vibe-hacker first, then apply to sound-byte-libs.

## Context

The current planning system works but has limitations around metadata extraction, document evolution after locking, and adding new document types. FDP-005 designs a v2 system that addresses these issues. We'll implement incrementally, testing each phase on vibe-hacker before moving to sound-byte-libs.

## Tasks

### Phase 1: Core Infrastructure

- [ ] Add `pyyaml` note to docs (it's stdlib-available via `yaml` module check, or document dependency)
- [ ] Create `scripts/frontmatter.py` - shared frontmatter parsing/rendering utilities
- [ ] Update `scripts/config.py` - add type definitions loader, version tracking, backwards compat for old config format
- [ ] Create default type definitions (inline defaults when no config exists)

### Phase 2: Update Existing Scripts for Frontmatter

- [ ] Update `templates/adr.md` - add frontmatter block
- [ ] Update `templates/fdp.md` - add frontmatter block
- [ ] Update `templates/action-plan.md` - add frontmatter block
- [ ] Update `scripts/new.py` - generate frontmatter on creation
- [ ] Update `scripts/edit.py` - parse frontmatter for status check
- [ ] Update `scripts/archive.py` - update frontmatter status field
- [ ] Update `scripts/update-status.py` - update frontmatter and body status
- [ ] Update `scripts/list.py` - parse frontmatter for reliable listing

### Phase 3: New Scripts

- [ ] Create `scripts/append.py` - add addendum to any document
- [ ] Create `scripts/supersede.py` - create superseding doc, update both docs
- [ ] Create `scripts/relate.py` - add related document links (with --bidirectional flag)

### Phase 4: Reports Document Type

- [ ] Create `templates/report.md` - new template with frontmatter
- [ ] Test creating, editing, archiving reports
- [ ] Update SKILL.md with report documentation

### Phase 5: Migration System

- [ ] Create `migrations/` directory structure
- [ ] Create `migrations/manifest.json`
- [ ] Create `scripts/vibe-doc.py` - migration CLI
- [ ] Create `migrations/v0.1.0/` - baseline (no migration script needed)
- [ ] Create `migrations/v0.2.0/migrate.py` - frontmatter migration
- [ ] Create `migrations/v0.2.0/CHANGELOG.md`

### Phase 6: Test on vibe-hacker

- [ ] Run `vibe-doc status` - verify version detection
- [ ] Run `vibe-doc upgrade --dry-run` - review planned changes
- [ ] Run `vibe-doc upgrade` - migrate vibe-hacker docs
- [ ] Verify all existing docs have frontmatter
- [ ] Verify all existing docs have addenda section
- [ ] Test `new.py` creates docs with frontmatter
- [ ] Test `append.py` on an accepted ADR
- [ ] Test `supersede.py` creates linked documents
- [ ] Test `list.py` still works correctly
- [ ] Verify protected paths still work

### Phase 7: Test on sound-byte-libs

- [ ] Copy/install updated planning plugin to sound-byte-libs
- [ ] Run `vibe-doc status` - check if planning docs exist
- [ ] Run `vibe-doc upgrade --dry-run` - review planned changes
- [ ] Run `vibe-doc upgrade` - migrate sound-byte-libs docs (if any)
- [ ] Create a test ADR to verify new doc creation
- [ ] Create a test Report to verify new type works
- [ ] Test addendum workflow

### Phase 8: Documentation & Cleanup

- [ ] Update SKILL.md with all new commands
- [ ] Update README.md with v2 features
- [ ] Update `templates/vibe-hacker.json.example` with new config format
- [ ] Remove any temporary test documents

## Notes

**Open questions resolved (from FDP-005):**
1. Related links: One-way by default, `--bidirectional` flag available
2. Addenda author: Optional, user can add manually if desired
3. Auto-archive on supersede: No, just mark superseded and prompt
4. Number formatting: Make configurable in type definition

**Dependencies:**
- PyYAML: Check if available, document if external dependency needed

## Completion Criteria

- [ ] All vibe-hacker planning docs have frontmatter and addenda sections
- [ ] Can create new docs of all types (ADR, FDP, AP, Report) with proper frontmatter
- [ ] Can append addenda to locked documents
- [ ] Can supersede documents with proper bidirectional linking
- [ ] `vibe-doc upgrade` successfully migrates sound-byte-libs
- [ ] SKILL.md documents all new functionality

## References

- FDP-005: Planning System v2 - Frontmatter, Addenda, and Migrations
- ADR-003: Script Language Choice (Python for planning scripts)

---

## Addenda
