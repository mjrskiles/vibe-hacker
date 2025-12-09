# FDP-002: Protected Paths System

## Status

Proposed

## Summary

A tiered path protection system that prevents accidental modification of planning documents, archived decisions, and other files that should remain immutable or require special handling. The system uses hooks to intercept edits and either warn, redirect to a CLI tool/skill, or block entirely.

## Motivation

Claude agents are helpful but sometimes too eager to "keep things consistent." This causes problems:

1. **Historical docs get rewritten** - When designs change, Claude updates old ADRs/FDPs to match the new design, destroying the historical record of what was decided and why at that point in time
2. **Archives get modified** - Completed action plans, superseded decisions, and archived docs should be read-only snapshots
3. **Planning structure erodes** - Without guardrails, planning docs get created/moved/renamed inconsistently

The goal is to preserve the value of planning documentation as a historical record while still allowing Claude to help with current planning work.

## Detailed Design

### Protection Tiers

Three levels of protection, configurable per path pattern:

| Tier | Behavior | Use Case |
|------|----------|----------|
| `readonly` | Block edits entirely, explain why | Archives, superseded docs, historical snapshots |
| `guided` | Warn and suggest using a skill/CLI instead | Active planning docs (use `/plan` skill) |
| `remind` | Allow edit but show contextual reminder | Templates, examples, docs with special rules |

### Configuration

Add `protected_paths` section to `vibe-hacker.json`:

```json
{
  "greenfield_mode": true,
  "priming": { ... },
  "protected_paths": {
    "planning_root": "docs/planning",
    "rules": [
      {
        "pattern": "docs/planning/archive/**",
        "tier": "readonly",
        "message": "Archived documents are read-only historical records."
      },
      {
        "pattern": "docs/planning/decision-records/[0-9]*.md",
        "tier": "readonly",
        "message": "Accepted ADRs are immutable. To supersede, create a new ADR."
      },
      {
        "pattern": "docs/planning/feature-designs/*.md",
        "tier": "guided",
        "message": "Use the /plan skill to modify feature designs.",
        "skill": "plan"
      },
      {
        "pattern": "docs/planning/action-plans/AP-*.md",
        "tier": "guided",
        "message": "Use the /plan skill to update action plans.",
        "skill": "plan"
      },
      {
        "pattern": "templates/**",
        "tier": "remind",
        "message": "This is a template file. Ensure placeholders like {{variable}} are preserved."
      }
    ]
  }
}
```

### Implementation Strategy

All protection is handled via a PreToolUse hook provided by the plugin. This keeps the feature self-contained - users configure protection in `vibe-hacker.json`, and the plugin enforces it. No changes to the user's `.claude/settings.json` required.

#### PreToolUse Hook

The hook intercepts Edit/Write calls *before* they execute:

```
PreToolUse (Edit|Write)
       │
       ▼
check-protected-paths.sh
       │
       ├── Parse file_path from tool input
       ├── Load rules from vibe-hacker.json
       ├── Match path against protected_paths rules
       ├── (Optional) Parse document status from file content
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ readonly?  → JSON: permissionDecision: "deny" + message      │
│ guided?    → JSON: permissionDecision: "deny" + skill hint   │
│ remind?    → stderr warning, exit 0 (allow)                  │
│ no match?  → exit 0 (allow)                                  │
└──────────────────────────────────────────────────────────────┘
```

To block an edit, the hook outputs JSON:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "This ADR has status 'Accepted'. Use /plan supersede ADR-001 to create a new ADR."
  }
}
```

#### Why PreToolUse, Not PostToolUse

- **PreToolUse** blocks the edit *before* it happens - no rollback needed
- **PostToolUse** runs *after* the edit completes - would require undoing changes
- PreToolUse = edits to protected paths never happen in the first place

#### Why Not Native Permissions

Claude Code has a native permission system (`deny` rules in settings.json), but:
- Requires users to manually edit their settings.json
- Mixes plugin config with user/project config
- Can't do dynamic checks (status-based protection)
- Plugin should be self-contained

### Planning Skill Integration

For `guided` tier paths, the hook suggests using the planning skill (`skills/planning/`).

The skill provides Python scripts for structured document management:

```bash
# Create new documents with auto-numbering
python3 skills/planning/scripts/new.py fdp "Widget System"
python3 skills/planning/scripts/new.py adr "Use PostgreSQL"
python3 skills/planning/scripts/new.py ap "Implement login"

# Archive completed/superseded documents
python3 skills/planning/scripts/archive.py FDP-001
python3 skills/planning/scripts/archive.py ADR-002

# List documents with status
python3 skills/planning/scripts/list.py
python3 skills/planning/scripts/list.py --type adr --include-archived
```

The skill handles:
- Auto-numbering (finds next available number per type)
- Template-based creation (consistent structure)
- Archive management (moves to archive/, updates status, adds date)
- Status extraction and listing

### Archive Structure

```
docs/planning/
├── action-plans/
│   ├── AP-001-*.md          # Active plans (guided)
│   └── archive/             # Completed plans (readonly)
│       └── AP-001-*.md
├── decision-records/
│   ├── template.md          # Template (remind)
│   ├── 001-*.md             # Accepted ADRs (readonly)
│   └── archive/             # Superseded ADRs (readonly)
│       └── 001-*.md
└── feature-designs/
    ├── FDP-001-*.md         # Active designs (guided)
    └── archive/             # Implemented/abandoned (readonly)
        └── FDP-001-*.md
```

### Status-Based Protection

Some documents transition from editable to readonly based on status:

| Document Type | Editable When | Readonly When |
|---------------|---------------|---------------|
| ADR | Status: Proposed | Status: Accepted, Deprecated, Superseded |
| FDP | Status: Proposed, In Progress | Status: Implemented, Abandoned |
| Action Plan | Status: Active | Status: Completed, Abandoned |

The check script could parse YAML frontmatter or the Status section to determine protection level dynamically.

### Error Messages

Clear, actionable messages when edits are blocked:

```
╔══════════════════════════════════════════════════════════════╗
║ PROTECTED PATH: docs/planning/decision-records/001-greenfield-mode.md
║
║ This ADR has status "Accepted" and is now immutable.
║ Historical decisions should not be modified after acceptance.
║
║ To make changes:
║   • If the decision is wrong: Create a new ADR that supersedes this one
║   • If clarification needed: Add a "Clarifications" section (allowed)
║   • To see history: git log docs/planning/decision-records/001-*.md
║
║ Use: /plan supersede ADR-001 "New approach to greenfield mode"
╚══════════════════════════════════════════════════════════════╝
```

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `scripts/check-protected-paths.sh` | Create | Protection check script |
| `hooks/hooks.json` | Modify | Add PreToolUse hook for protected paths |
| `commands/plan.md` | Create | Planning skill command |
| `agents/planner.md` | Create | Planning agent (optional) |
| `templates/vibe-hacker.json.example` | Modify | Add protected_paths example |
| `docs/ARCHITECTURE.md` | Modify | Document protection system |

## Implementation Phases

### Phase 1: Basic Protection
- Implement PreToolUse hook for `readonly` tier
- Simple glob matching against configured patterns
- Block message with explanation

### Phase 2: Guided Tier
- Add `guided` tier with skill suggestions
- Create basic `/plan` command
- Implement archive management

### Phase 3: Dynamic Status Detection
- Parse document status from content
- Auto-promote to readonly when status changes
- Add status transition commands to `/plan`

## Alternatives Considered

### Git hooks instead of Claude hooks

Use git pre-commit hooks to block changes to protected files.

**Rejected**: Blocks at commit time, not edit time. Claude would still make the changes, user would see failures at commit. Also doesn't provide the guided workflow.

### Directory permissions

Use filesystem permissions to make files readonly.

**Rejected**: Too coarse-grained. Prevents legitimate edits (typo fixes, clarifications). Doesn't integrate with Claude's workflow.

### CLAUDE.md instructions only

Just tell Claude not to edit certain files in CLAUDE.md.

**Rejected**: Relies on Claude following instructions perfectly. Instructions get forgotten in long sessions or after compaction. No enforcement.

### Separate repo for archives

Move archived docs to a separate repository.

**Rejected**: Loses the convenience of having all planning docs together. Makes cross-referencing harder.

## Open Questions

1. **Clarification sections** - Should we allow appending "Clarification" sections to readonly ADRs without triggering protection?
2. **Override mechanism** - Should there be a way to force-edit protected files? (e.g., `--force` flag, user confirmation)
3. **Git integration** - Should archiving create a git tag or special commit message?
4. **Frontmatter vs heading** - Parse status from YAML frontmatter or markdown heading?
5. **Glob library** - Use bash glob expansion or bring in a proper glob library for complex patterns?

## References

- [ADR-001: Greenfield Mode](../decision-records/001-greenfield-mode.md) - Related protection concept
- [Claude Code Hooks Guide](https://docs.anthropic.com/claude-code/hooks)
