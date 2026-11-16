"""
Frontmatter parsing and rendering utilities for planning documents.

Provides functions to parse YAML frontmatter from markdown documents
and render frontmatter back to YAML format.
"""

import re
from datetime import date
from typing import Optional

# Try to import yaml, fall back to basic parsing if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Frontmatter delimiters
FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)

# Addenda section markers
ADDENDA_SEPARATOR = "\n\n---\n\n## Addenda\n"
ADDENDA_PATTERN = re.compile(r'\n---\n\n## Addenda\n', re.IGNORECASE)

# The first top-level Status heading and the blank lines under it
STATUS_HEADING_PATTERN = re.compile(r'^## Status[ \t]*\n(?:[ \t]*\n)*', re.MULTILINE)

# A Status paragraph that is only the status: one to three words
BARE_STATUS_PATTERN = re.compile(r'[A-Za-z]+(?: [A-Za-z]+){0,2}')


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract frontmatter and body from a markdown document.

    Args:
        content: Full document content

    Returns:
        Tuple of (frontmatter_dict, body_content)
        Returns ({}, content) if no frontmatter found
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = content[match.end():]

    if HAS_YAML:
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            return frontmatter or {}, body
        except yaml.YAMLError:
            return {}, content
    else:
        # Basic fallback parsing for simple key: value pairs
        frontmatter = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                # Handle null/empty values
                if value.lower() in ('null', '~', ''):
                    value = None
                # Handle lists (basic)
                elif value.startswith('[') and value.endswith(']'):
                    items = value[1:-1].split(',')
                    value = [item.strip().strip('"\'') for item in items if item.strip()]
                # Strip quotes
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                frontmatter[key] = value
        return frontmatter, body


def render_frontmatter(data: dict) -> str:
    """
    Render a frontmatter dictionary to YAML string with delimiters.

    Args:
        data: Dictionary of frontmatter fields

    Returns:
        YAML frontmatter string including --- delimiters
    """
    if HAS_YAML:
        # Custom representer for None to output 'null'
        def represent_none(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')

        yaml.add_representer(type(None), represent_none)
        yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return f"---\n{yaml_content}---\n"
    else:
        # Basic fallback rendering
        lines = ['---']
        for key, value in data.items():
            if value is None:
                lines.append(f"{key}: null")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{key}: []")
                else:
                    lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            else:
                lines.append(f"{key}: {value}")
        lines.append('---')
        return '\n'.join(lines) + '\n'


def update_frontmatter(content: str, updates: dict) -> str:
    """
    Update specific fields in a document's frontmatter.

    Args:
        content: Full document content
        updates: Dictionary of fields to update

    Returns:
        Updated document content
    """
    frontmatter, body = parse_frontmatter(content)
    frontmatter.update(updates)
    return render_frontmatter(frontmatter) + body


def get_frontmatter_field(content: str, field: str, default=None):
    """
    Get a specific field from document frontmatter.

    Args:
        content: Full document content
        field: Field name to retrieve
        default: Default value if field not found

    Returns:
        Field value or default
    """
    frontmatter, _ = parse_frontmatter(content)
    return frontmatter.get(field, default)


def has_frontmatter(content: str) -> bool:
    """Check if document has frontmatter."""
    return bool(FRONTMATTER_PATTERN.match(content))


def has_addenda_section(content: str) -> bool:
    """Check if document has an addenda section."""
    return bool(ADDENDA_PATTERN.search(content))


def stamp_modified(frontmatter: dict) -> None:
    """
    Set a frontmatter dictionary's modified date to today.

    The value is a date, not a string, so that YAML writes it unquoted.
    """
    frontmatter['modified'] = date.today()


def format_entry(title: str, body: str) -> str:
    """
    Format a dated entry, as used for addenda and log entries.

    Args:
        title: Entry title (without date)
        body: Entry content

    Returns:
        The entry: a level-3 heading with today's date, then the body
    """
    return f"### {date.today().isoformat()}: {title}\n\n{body.rstrip()}\n"


def append_addendum(content: str, title: str, body: str) -> str:
    """
    Add an addendum to a document.

    Creates the addenda section if it doesn't exist.
    Updates the modified date in frontmatter.

    Args:
        content: Full document content
        title: Title for the addendum (without date)
        body: Addendum content

    Returns:
        Updated document content
    """
    frontmatter, doc_body = parse_frontmatter(content)
    if frontmatter:
        stamp_modified(frontmatter)
        content = render_frontmatter(frontmatter) + doc_body

    entry = format_entry(title, body)
    if has_addenda_section(content):
        return content.rstrip() + "\n\n" + entry
    return content.rstrip() + ADDENDA_SEPARATOR + "\n" + entry


def set_body_status(content: str, new_status: str) -> tuple[str, bool]:
    """
    Set the status shown under a document's first "## Status" heading.

    A paragraph that is only a status (one line of one to three words) is
    replaced. Any other paragraph is prose and is kept whole: the status goes
    on a line of its own above it. Later "## Status" headings and deeper
    headings such as "### Status" are left alone.

    Args:
        content: Full document content
        new_status: Status to show (any case)

    Returns:
        Tuple of (updated content, whether a Status section was found)
    """
    heading = STATUS_HEADING_PATTERN.search(content)
    if not heading:
        return content, False

    shown = new_status.strip().capitalize()
    start = heading.end()
    rest = content[start:]

    paragraph = []
    for line in rest.split('\n'):
        if not line.strip() or line.startswith('#'):
            break
        paragraph.append(line)

    if len(paragraph) == 1 and BARE_STATUS_PATTERN.fullmatch(paragraph[0].strip()):
        return content[:start] + shown + rest[len(paragraph[0]):], True
    return content[:start] + shown + "\n\n" + rest, True


def document_status(content: str) -> Optional[str]:
    """
    Get a document's status: frontmatter first, then the Status section.

    Returns:
        Status string or None if the document states none
    """
    frontmatter, _ = parse_frontmatter(content)
    if frontmatter and frontmatter.get('status'):
        return str(frontmatter['status'])
    return extract_status_from_body(content)


def set_status(content: str, new_status: str, extra_fields: Optional[dict] = None) -> str:
    """
    Set a document's status in its frontmatter and its Status section.

    Args:
        content: Full document content
        new_status: New status (stored lowercase in frontmatter)
        extra_fields: Further frontmatter fields to set in the same write

    Returns:
        Updated document content

    Raises:
        ValueError: If the document has neither frontmatter nor a Status section
    """
    frontmatter, body = parse_frontmatter(content)
    if frontmatter:
        frontmatter['status'] = new_status.strip().lower()
        frontmatter.update(extra_fields or {})
        stamp_modified(frontmatter)
        content = render_frontmatter(frontmatter) + body

    content, found = set_body_status(content, new_status)
    if not frontmatter and not found:
        raise ValueError("Document has neither frontmatter nor a Status section")
    return content


def insert_note_under_title(content: str, note: str) -> str:
    """
    Put a one-line blockquote under a document's H1 heading.

    Without an H1 the note goes at the top of the body.

    Args:
        content: Full document content
        note: Note text, one line

    Returns:
        Updated document content
    """
    block = f"> {note}\n"
    frontmatter = FRONTMATTER_PATTERN.match(content)
    body_start = frontmatter.end() if frontmatter else 0

    title = re.compile(r'^# [^\n]*\n', re.MULTILINE).search(content, body_start)
    if title:
        return content[:title.end()] + "\n" + block + content[title.end():]
    return content[:body_start] + block + "\n" + content[body_start:].lstrip('\n')


def create_frontmatter(
    doc_type: str,
    doc_id: str,
    status: str,
    created: Optional[str] = None,
    supersedes: Optional[str] = None,
    related: Optional[list] = None
) -> dict:
    """
    Create a standard frontmatter dictionary for a new document.

    Args:
        doc_type: Document type (adr, fdp, ap, report)
        doc_id: Display ID (ADR-001, FDP-002, etc.)
        status: Initial status
        created: Creation date (defaults to today)
        supersedes: ID of document this supersedes (optional)
        related: List of related document IDs (optional)

    Returns:
        Frontmatter dictionary
    """
    today = date.today().isoformat()
    return {
        'type': doc_type,
        'id': doc_id,
        'status': status,
        'created': created or today,
        'modified': today,
        'supersedes': supersedes,
        'superseded_by': None,
        'obsoleted_by': None,
        'related': related or [],
    }


def extract_status_from_body(content: str) -> Optional[str]:
    """
    Extract status from the ## Status section in document body.

    Args:
        content: Document content (body only, no frontmatter)

    Returns:
        Status string or None if not found
    """
    # Look for ## Status section
    status_match = re.search(r'^## Status\s*\n+([^\n#]+)', content, re.MULTILINE)
    if status_match:
        return status_match.group(1).strip()
    return None


def extract_title_from_body(content: str) -> Optional[str]:
    """
    Extract title from the H1 heading in document body.

    Args:
        content: Document content

    Returns:
        Title string (without ID prefix) or None if not found
    """
    # Look for # heading, optionally with ID prefix
    title_match = re.search(r'^# (?:[A-Z]+-\d+:\s*)?(.+)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return None


def extract_date_from_body(content: str) -> Optional[str]:
    """
    Extract date from ## Date or ## Created section in document body.

    Args:
        content: Document content

    Returns:
        Date string (ISO format) or None if not found
    """
    # Look for ## Date or ## Created section
    date_match = re.search(r'^## (?:Date|Created)\s*\n+(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
    if date_match:
        return date_match.group(1)
    return None
