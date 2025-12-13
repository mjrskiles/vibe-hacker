---
type: fdp
id: FDP-005
status: proposed
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# FDP-005: Planning System v2 - Frontmatter, Addenda, and Migrations

## Status

Proposed

## Summary

Evolve the planning system to support YAML frontmatter for structured metadata, an addenda system for appending to locked documents, document relationship tracking (supersedes/obsoletes), extensible document types, and a versioned migration system (`vibe-doc`) for upgrading existing projects.

## Motivation

The current planning system works well for basic document management but has limitations:

1. **Metadata extraction is fragile** - Parsing `## Status` sections and H1 titles via regex is brittle
2. **Locked documents can't evolve** - Once an ADR is accepted, there's no way to add clarifications or updates
3. **No document relationships** - Can't express "ADR-005 supersedes ADR-001" in a structured way
4. **Hardcoded document types** - Adding new types (e.g., Reports) requires script changes
5. **No upgrade path** - As the plugin evolves, users have no way to migrate their existing documents

This proposal addresses all five limitations with a cohesive design.

## Detailed Design

### Overview

The v2 system introduces:

1. **YAML Frontmatter** - Structured metadata at the top of every document
2. **Addenda Section** - Append-only section for updates to locked documents
3. **Document Relationships** - `supersedes`, `superseded_by`, `obsoleted_by`, `related` fields
4. **Extensible Types** - Document types defined in config, not code
5. **`vibe-doc` Migration System** - Versioned migrations for project upgrades

### Components

#### 1. Frontmatter Format

All planning documents will use YAML frontmatter:

```yaml
---
type: adr
id: ADR-001
status: accepted
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# ADR-001: Use PostgreSQL for Persistence

## Context
...
```

**Frontmatter fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Document type identifier (adr, fdp, ap, report) |
| `id` | string | Yes | Display ID (ADR-001, FDP-003, etc.) |
| `status` | string | Yes | Current lifecycle status |
| `created` | date | Yes | ISO date of creation |
| `modified` | date | Yes | ISO date of last modification |
| `supersedes` | string/null | No | ID of document this one replaces |
| `superseded_by` | string/null | No | ID of document that replaced this one |
| `obsoleted_by` | string/null | No | ID or reason for obsolescence |
| `related` | list | No | IDs of related documents |

#### 2. Addenda System

Documents have an append-only section for updates after locking:

```markdown
---
type: adr
id: ADR-001
status: accepted
...
---

# ADR-001: Use PostgreSQL for Persistence

## Context
...original frozen content...

## Decision
...

## Consequences
...

---

## Addenda

### 2025-02-15: Performance Observations

After 2 months in production, read replicas handle our query load well.
The connection pooling strategy from the original decision is working.

### 2025-04-20: Migration Tip

When migrating from SQLite, use `pg_dump --format=custom` for best results.
```

**Key rules:**
- Horizontal rule (`---`) separates frozen content from addenda
- Each addendum has a dated H3 heading
- Addenda can be added to ANY document regardless of status
- Adding an addendum updates the `modified` date in frontmatter
- Original content above the separator is never modified

#### 3. Document Relationships

**Supersedes**: A new document replaces an older one's decision/design.
```yaml
# In ADR-005:
supersedes: ADR-001

# Script automatically updates ADR-001:
superseded_by: ADR-005
status: superseded  # if not already archived
```

**Obsoleted**: The concern no longer applies (feature removed, requirement changed).
```yaml
obsoleted_by: "Feature removed in v2.0"
# or
obsoleted_by: FDP-010  # if another doc explains why
```

**Related**: Informational links (not bidirectional by default).
```yaml
related:
  - ADR-002
  - FDP-003
```

#### 4. Extensible Document Types

Document types are defined in configuration rather than hardcoded:

```json
{
  "planning": {
    "types": {
      "adr": {
        "name": "Architecture Decision Record",
        "dir": "decision-records",
        "prefix": "",
        "filename_format": "{number:03d}-{slug}.md",
        "id_format": "ADR-{number:03d}",
        "template": "adr.md",
        "statuses": {
          "initial": "proposed",
          "editable": ["proposed"],
          "final": ["accepted"],
          "archive_triggers": ["deprecated", "superseded"]
        }
      },
      "fdp": {
        "name": "Feature Design Proposal",
        "dir": "feature-designs",
        "prefix": "FDP-",
        "filename_format": "FDP-{number:03d}-{slug}.md",
        "id_format": "FDP-{number:03d}",
        "template": "fdp.md",
        "statuses": {
          "initial": "proposed",
          "editable": ["proposed", "in progress"],
          "final": ["implemented"],
          "archive_triggers": ["implemented", "abandoned"]
        }
      },
      "ap": {
        "name": "Action Plan",
        "dir": "action-plans",
        "prefix": "AP-",
        "filename_format": "AP-{number:03d}-{slug}.md",
        "id_format": "AP-{number:03d}",
        "template": "action-plan.md",
        "statuses": {
          "initial": "active",
          "editable": ["active"],
          "final": ["completed"],
          "archive_triggers": ["completed", "abandoned"]
        }
      },
      "report": {
        "name": "Report",
        "dir": "reports",
        "prefix": "RPT-",
        "filename_format": "RPT-{number:03d}-{slug}.md",
        "id_format": "RPT-{number:03d}",
        "template": "report.md",
        "statuses": {
          "initial": "draft",
          "editable": ["draft"],
          "final": ["published"],
          "archive_triggers": ["superseded", "obsoleted"]
        }
      }
    }
  }
}
```

**Type configuration fields:**

| Field | Description |
|-------|-------------|
| `name` | Human-readable name for display |
| `dir` | Subdirectory under planning root |
| `prefix` | Prefix in filename (empty string for ADRs) |
| `filename_format` | Python format string for filename |
| `id_format` | Python format string for display ID |
| `template` | Template filename |
| `statuses.initial` | Status assigned on creation |
| `statuses.editable` | Statuses that allow editing |
| `statuses.final` | Statuses that lock the document |
| `statuses.archive_triggers` | Statuses that suggest archiving |

#### 5. `vibe-doc` Migration System

A versioned migration system for upgrading project configurations and documents.

**Concept:**
```
plugins/planning/
└── migrations/
    ├── manifest.json          # Lists all versions and their migrations
    ├── v0.1.0/                # Initial version (no migrations)
    ├── v0.2.0/
    │   ├── migrate.py         # Migration script
    │   └── CHANGELOG.md       # What changed
    └── v0.3.0/
        ├── migrate.py
        └── CHANGELOG.md
```

**Manifest format:**
```json
{
  "versions": [
    {
      "version": "0.1.0",
      "date": "2025-12-01",
      "description": "Initial release"
    },
    {
      "version": "0.2.0",
      "date": "2025-12-15",
      "description": "Add frontmatter, addenda, document relationships",
      "migration": "v0.2.0/migrate.py",
      "breaking": true
    }
  ],
  "current": "0.2.0"
}
```

**Migration script interface:**
```python
#!/usr/bin/env python3
"""
Migration: v0.1.0 -> v0.2.0
Adds frontmatter to all planning documents.
"""

def check_applicable(project_dir: str) -> bool:
    """Return True if this migration should run."""
    pass

def dry_run(project_dir: str) -> list[str]:
    """Return list of changes that would be made."""
    pass

def migrate(project_dir: str) -> bool:
    """Perform the migration. Return True on success."""
    pass

def rollback(project_dir: str) -> bool:
    """Undo the migration if possible."""
    pass
```

**CLI command:**
```bash
# Check current version and available upgrades
vibe-doc status

# Show what a migration would do
vibe-doc upgrade --dry-run

# Perform migration
vibe-doc upgrade

# Upgrade to specific version
vibe-doc upgrade --to 0.2.0

# Rollback (if supported)
vibe-doc rollback
```

**Version tracking:**
The plugin tracks the project's current version in `.claude/vibe-hacker.json`:
```json
{
  "planning": {
    "version": "0.1.0",
    ...
  }
}
```

### Implementation Details

#### Frontmatter Parsing

Use Python's built-in capabilities:
```python
import yaml
import re

FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract frontmatter and body from document."""
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]
        return frontmatter, body
    return {}, content

def render_frontmatter(data: dict) -> str:
    """Render frontmatter dict to YAML string."""
    return f"---\n{yaml.dump(data, default_flow_style=False, sort_keys=False)}---\n"
```

#### Addenda Insertion

```python
ADDENDA_SEPARATOR = "\n---\n\n## Addenda\n"
ADDENDA_SECTION = re.compile(r'\n---\n\n## Addenda\n', re.IGNORECASE)

def append_addendum(content: str, title: str, body: str) -> str:
    """Add an addendum to a document."""
    date = datetime.now().strftime("%Y-%m-%d")
    addendum = f"\n### {date}: {title}\n\n{body}\n"

    if ADDENDA_SECTION.search(content):
        # Append to existing addenda section
        return content + addendum
    else:
        # Create addenda section
        return content + ADDENDA_SEPARATOR + addendum
```

#### Supersede Operation

```python
def supersede_document(old_id: str, new_title: str) -> str:
    """Create a new document that supersedes an old one."""
    # 1. Parse old document to get its type
    old_doc = find_document(old_id)
    doc_type = old_doc.frontmatter['type']

    # 2. Create new document
    new_path = create_document(doc_type, new_title)
    new_id = extract_id(new_path)

    # 3. Update new document's frontmatter
    update_frontmatter(new_path, {'supersedes': old_id})

    # 4. Update old document's frontmatter
    update_frontmatter(old_doc.path, {
        'superseded_by': new_id,
        'status': 'superseded'
    })

    # 5. Optionally add addendum to old document
    append_addendum(old_doc.path,
        "Superseded",
        f"This document has been superseded by [{new_id}]({new_path}).")

    return new_path
```

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `skills/planning/scripts/config.py` | Modify | Load type definitions from config, add version tracking |
| `skills/planning/scripts/new.py` | Modify | Generate frontmatter, use type config |
| `skills/planning/scripts/edit.py` | Modify | Parse frontmatter for status |
| `skills/planning/scripts/archive.py` | Modify | Update frontmatter status |
| `skills/planning/scripts/update-status.py` | Modify | Update frontmatter and body status |
| `skills/planning/scripts/list.py` | Modify | Parse frontmatter for listing |
| `skills/planning/scripts/append.py` | Create | Add addendum to any document |
| `skills/planning/scripts/supersede.py` | Create | Create superseding document, update relationships |
| `skills/planning/scripts/relate.py` | Create | Add related document links |
| `skills/planning/scripts/vibe-doc.py` | Create | Migration CLI tool |
| `skills/planning/templates/adr.md` | Modify | Add frontmatter template |
| `skills/planning/templates/fdp.md` | Modify | Add frontmatter template |
| `skills/planning/templates/action-plan.md` | Modify | Add frontmatter template |
| `skills/planning/templates/report.md` | Create | New report template with frontmatter |
| `migrations/manifest.json` | Create | Version manifest |
| `migrations/v0.2.0/migrate.py` | Create | Frontmatter migration script |
| `migrations/v0.2.0/CHANGELOG.md` | Create | Migration changelog |
| `SKILL.md` | Modify | Document new commands and frontmatter format |

## Implementation Phases

### Phase 1: Core Frontmatter Support
- Add frontmatter parsing utilities to `config.py`
- Update `new.py` to generate frontmatter
- Update `edit.py`, `archive.py`, `update-status.py` to use frontmatter
- Update `list.py` to parse frontmatter
- Update all templates with frontmatter

### Phase 2: Addenda and Relationships
- Create `append.py` for addenda
- Create `supersede.py` for document supersession
- Create `relate.py` for related links (optional)
- Add relationship validation

### Phase 3: Extensible Types
- Refactor scripts to use type configuration
- Add `report` type with template
- Update `SKILL.md` documentation

### Phase 4: Migration System
- Create migration framework (`vibe-doc.py`)
- Create v0.2.0 migration for frontmatter conversion
- Add version tracking to config
- Document upgrade process

## v0.2.0 Migration: Detailed Plan

This section documents the specific migration from v0.1.0 to v0.2.0.

### Configuration Migration

**Before (`vibe-hacker.json`):**
```json
{
  "planning": {
    "subdirs": {
      "adr": "decision-records",
      "fdp": "feature-designs",
      "ap": "action-plans"
    }
  }
}
```

**After:**
```json
{
  "planning": {
    "version": "0.2.0",
    "types": {
      "adr": {
        "name": "Architecture Decision Record",
        "dir": "decision-records",
        "prefix": "",
        "filename_format": "{number:03d}-{slug}.md",
        "id_format": "ADR-{number:03d}",
        "template": "adr.md",
        "statuses": {
          "initial": "proposed",
          "editable": ["proposed"],
          "final": ["accepted"],
          "archive_triggers": ["deprecated", "superseded"]
        }
      },
      "fdp": { ... },
      "ap": { ... },
      "report": { ... }
    }
  }
}
```

### Document Migration

For each existing document:

1. **Extract existing metadata** from markdown:
   - Type from filename pattern
   - ID from H1 heading
   - Status from `## Status` section
   - Created date from `## Date` or `## Created` section

2. **Generate frontmatter**:
   ```yaml
   ---
   type: adr
   id: ADR-001
   status: accepted
   created: 2025-12-01
   modified: 2025-12-13
   supersedes: null
   superseded_by: null
   obsoleted_by: null
   related: []
   ---
   ```

3. **Prepend to document** (preserve all existing content)

4. **Add empty addenda section** at the end:
   ```markdown

   ---

   ## Addenda
   ```

### Migration Script Logic

```python
def migrate(project_dir: str) -> bool:
    config = load_config(project_dir)
    planning_root = get_planning_root(config)

    # 1. Migrate configuration
    new_config = convert_config_to_v2(config)
    save_config(project_dir, new_config)

    # 2. Find all planning documents
    docs = find_all_planning_docs(planning_root)

    # 3. Migrate each document
    for doc in docs:
        # Parse existing content
        content = read_file(doc.path)
        doc_type = infer_type(doc.path)
        doc_id = extract_id_from_heading(content)
        status = extract_status(content)
        created = extract_date(content) or get_file_created_date(doc.path)

        # Generate frontmatter
        frontmatter = {
            'type': doc_type,
            'id': doc_id,
            'status': status.lower(),
            'created': created,
            'modified': datetime.now().strftime('%Y-%m-%d'),
            'supersedes': None,
            'superseded_by': None,
            'obsoleted_by': None,
            'related': []
        }

        # Prepend frontmatter, append addenda section
        new_content = render_frontmatter(frontmatter) + content
        if not has_addenda_section(new_content):
            new_content += "\n\n---\n\n## Addenda\n"

        write_file(doc.path, new_content)

    return True
```

## Alternatives Considered

### 1. Separate Addenda Files
Instead of an addenda section, store addenda as separate files: `ADR-001.addendum-1.md`.

**Rejected because:**
- Fragments the document
- Harder to read as a whole
- More files to manage
- The inline approach is simpler and keeps context together

### 2. JSON Frontmatter
Use JSON instead of YAML for frontmatter.

**Rejected because:**
- YAML is the industry standard for markdown frontmatter
- Better human readability
- Widely supported by tools (Jekyll, Hugo, Obsidian, etc.)

### 3. Database for Metadata
Store document metadata in a SQLite database instead of frontmatter.

**Rejected because:**
- Adds complexity
- Documents become dependent on external state
- Breaks the "documents are the source of truth" principle
- Harder to version control

### 4. One-Time Migration Script
Create a throwaway script for migration instead of a versioned system.

**Rejected because:**
- Future versions will also need migrations
- Other users may install at different versions
- A system pays for itself quickly

## Open Questions

1. **Bidirectional `related` links?**
   - Current design: one-way (A relates to B, B doesn't auto-relate to A)
   - Alternative: always bidirectional
   - Recommendation: Keep one-way, add `relate.py --bidirectional` flag

2. **Addenda author tracking?**
   - Could add `Added by: @username` to addenda
   - Useful for teams, maybe overkill for solo developers
   - Recommendation: Make it optional (user can add manually if desired)

3. **Auto-archive on supersede?**
   - When A supersedes B, should B be auto-archived?
   - Or just marked superseded but left in place?
   - Recommendation: Mark superseded, prompt user to archive

4. **Variable-width number formatting?**
   - Current: 3 digits (`001`)
   - What about 4+ digits (`0001`)?
   - Recommendation: Make configurable in type definition

## References

- [ADR GitHub Repository](https://adr.github.io/) - Lightweight ADR format
- [YAML Frontmatter Spec](https://jekyllrb.com/docs/front-matter/) - Jekyll's frontmatter format
- [RFC 822](https://datatracker.ietf.org/doc/html/rfc822) - Internet message format (inspiration for obsoletes/supersedes)
- FDP-002: Protected Paths System
- ADR-001: Greenfield Mode for Prototype Projects

## Michael's response

First of all, this is fantastic work so be proud.

1. Agreed

2. option for now

3. agreed

4. agreed