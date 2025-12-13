#!/usr/bin/env python3
"""
Archive a planning document.

Usage:
    archive.py <doc-id>

Examples:
    archive.py ADR-001
    archive.py FDP-002
    archive.py AP-003
    archive.py RPT-001

This will:
    1. Update the document's status to "archived" in frontmatter and body
    2. Add an "Archived" date to the body
    3. Move the file to the archive/ subdirectory
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from config import (
    get_project_dir,
    get_planning_root,
    get_type_config,
)
from frontmatter import parse_frontmatter, render_frontmatter


def parse_doc_id(doc_id: str) -> tuple[str, int]:
    """
    Parse a document ID into type and number.

    Args:
        doc_id: Document ID like 'ADR-001', 'FDP-002', 'AP-001', 'RPT-001'

    Returns:
        Tuple of (doc_type, number)

    Raises:
        ValueError: If ID format is not recognized
    """
    doc_id = doc_id.upper()

    patterns = [
        (r'^ADR-(\d+)$', 'adr'),
        (r'^FDP-(\d+)$', 'fdp'),
        (r'^AP-(\d+)$', 'ap'),
        (r'^RPT-(\d+)$', 'report'),
    ]

    for pattern, doc_type in patterns:
        match = re.match(pattern, doc_id)
        if match:
            return doc_type, int(match.group(1))

    raise ValueError(f"Invalid document ID: {doc_id}. Expected format: ADR-001, FDP-002, AP-003, or RPT-001")


def find_document(doc_type: str, number: int, project_dir: Path) -> Path | None:
    """Find a document by type and number (not in archive)."""
    type_config = get_type_config(doc_type)
    planning_root = project_dir / get_planning_root()
    doc_dir = planning_root / type_config['dir']

    if not doc_dir.exists():
        return None

    # Build pattern based on type config
    prefix = type_config.get('prefix', '')
    if prefix:
        pattern = re.compile(rf'^{re.escape(prefix)}(\d+)-.*\.md$')
    else:
        pattern = re.compile(r'^(\d+)-.*\.md$')

    for f in doc_dir.iterdir():
        if f.is_file():
            match = pattern.match(f.name)
            if match and int(match.group(1)) == number:
                return f

    return None


def update_status_in_content(content: str, new_status: str = "Archived") -> str:
    """Update status in both frontmatter and body."""
    today = date.today().isoformat()

    # Parse frontmatter
    frontmatter, body = parse_frontmatter(content)

    # Update frontmatter if present
    if frontmatter:
        frontmatter['status'] = new_status.lower()
        frontmatter['modified'] = today
        content = render_frontmatter(frontmatter) + body

    # Update body status section
    status_pattern = r'(## Status\s*\n\s*\n?)([^\n#]+)'

    def replace_status(match):
        prefix = match.group(1)
        return f"{prefix}{new_status}"

    content, count = re.subn(status_pattern, replace_status, content)

    # Add Archived date section if not present
    if '## Archived' not in content:
        archived_section = f"\n## Archived\n\n{today}\n"

        # Find position after Status section
        status_match = re.search(r'## Status\s*\n\s*\n?[^\n#]+\n', content)
        if status_match:
            insert_pos = status_match.end()
            content = content[:insert_pos] + archived_section + content[insert_pos:]

    return content


def archive_document(doc_id: str, project_dir: Path) -> Path:
    """Archive a planning document."""
    doc_type, number = parse_doc_id(doc_id)

    # Find the document
    filepath = find_document(doc_type, number, project_dir)
    if not filepath:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    # Check if already archived
    if 'archive' in filepath.parts:
        raise ValueError(f"Document is already archived: {filepath}")

    # Update status
    content = filepath.read_text()
    new_content = update_status_in_content(content)
    filepath.write_text(new_content)

    # Create archive directory
    archive_dir = filepath.parent / 'archive'
    archive_dir.mkdir(exist_ok=True)

    # Move to archive
    new_path = archive_dir / filepath.name
    if new_path.exists():
        raise FileExistsError(f"Archive destination already exists: {new_path}")

    shutil.move(str(filepath), str(new_path))

    return new_path


def main():
    parser = argparse.ArgumentParser(
        description='Archive a planning document.'
    )
    parser.add_argument(
        'doc_id',
        help='Document ID (e.g., ADR-001, FDP-002, AP-003, RPT-001)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        new_path = archive_document(args.doc_id, args.project_dir)
        print(f"Archived: {new_path}")
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
