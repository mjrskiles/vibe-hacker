#!/usr/bin/env python3
"""
Create a new document that supersedes an existing one.

This script:
1. Creates a new document of the same type
2. Sets the new document's 'supersedes' field to the old document's ID
3. Updates the old document's 'superseded_by' field
4. Updates the old document's status to 'superseded'
5. Adds an addendum to the old document noting the supersession

Usage:
    supersede.py <old-doc-id> "<new-title>"

Examples:
    supersede.py ADR-001 "Revised Database Strategy"
    supersede.py FDP-003 "Updated Authentication Design"
"""

import argparse
import sys
from pathlib import Path

from config import (
    find_document_by_id,
    format_doc_id,
    get_filename_pattern,
    get_project_dir,
    parse_doc_id,
)
from frontmatter import (
    append_addendum,
    parse_frontmatter,
    render_frontmatter,
    set_status,
    stamp_modified,
)
from new import create_document

SUPERSEDED_STATUS = 'superseded'


def update_old_document(filepath: Path, new_doc_id: str) -> None:
    """Update the old document with superseded_by and add addendum."""
    content = set_status(filepath.read_text(), SUPERSEDED_STATUS, {'superseded_by': new_doc_id})
    content = append_addendum(content, "Superseded", f"This document has been superseded by {new_doc_id}.")
    filepath.write_text(content)


def update_new_document(filepath: Path, old_doc_id: str) -> None:
    """Update the new document with supersedes field."""
    frontmatter, body = parse_frontmatter(filepath.read_text())

    if frontmatter:
        frontmatter['supersedes'] = old_doc_id
        stamp_modified(frontmatter)
        filepath.write_text(render_frontmatter(frontmatter) + body)


def supersede_document(old_doc_id: str, new_title: str, project_dir: Path) -> tuple[Path, Path]:
    """
    Create a new document that supersedes an existing one.

    Returns:
        Tuple of (new_document_path, old_document_path)
    """
    doc_type, _ = parse_doc_id(old_doc_id)
    old_filepath = find_document_by_id(old_doc_id, project_dir)

    # Check if old doc is already superseded
    old_content = old_filepath.read_text()
    old_frontmatter, _ = parse_frontmatter(old_content)
    if old_frontmatter and old_frontmatter.get('superseded_by'):
        existing = old_frontmatter['superseded_by']
        raise ValueError(f"{old_doc_id} is already superseded by {existing}")

    # Create new document
    new_filepath = create_document(doc_type, new_title, project_dir)

    # Extract new document ID from the created file
    new_content = new_filepath.read_text()
    new_frontmatter, _ = parse_frontmatter(new_content)
    new_doc_id = new_frontmatter.get('id') if new_frontmatter else None

    if not new_doc_id:
        # Fallback: extract from filename
        match = get_filename_pattern(doc_type).match(new_filepath.name)
        if match:
            new_doc_id = format_doc_id(doc_type, int(match.group(1)))

    # Update both documents
    update_new_document(new_filepath, old_doc_id)
    update_old_document(old_filepath, new_doc_id)

    return new_filepath, old_filepath


def main():
    parser = argparse.ArgumentParser(
        description='Create a new document that supersedes an existing one.'
    )
    parser.add_argument(
        'old_doc_id',
        help='ID of document to supersede (e.g., ADR-001)'
    )
    parser.add_argument(
        'new_title',
        help='Title for the new document'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        new_path, old_path = supersede_document(
            args.old_doc_id, args.new_title, args.project_dir
        )
        print(f"Created: {new_path}")
        print(f"Updated: {old_path}")
        print(f"\n{args.old_doc_id} is now superseded by the new document.")

    except (FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
