#!/usr/bin/env python3
"""
Archive a planning document.

Usage:
    archive.py <doc-id>

Examples:
    archive.py ADR-001
    archive.py FDP-002
    archive.py AP-003

This will:
    1. Update the document's Status to "Archived"
    2. Add an "Archived" date
    3. Move the file to the archive/ subdirectory
"""

import argparse
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from config import get_doc_dir


def get_doc_types() -> dict:
    """Get document type configurations with paths from config."""
    return {
        'adr': {
            'dir': get_doc_dir('adr'),
            'pattern': r'^(\d+)-.*\.md$',
            'id_pattern': r'^ADR-(\d+)$',
        },
        'fdp': {
            'dir': get_doc_dir('fdp'),
            'pattern': r'^FDP-(\d+)-.*\.md$',
            'id_pattern': r'^FDP-(\d+)$',
        },
        'ap': {
            'dir': get_doc_dir('ap'),
            'pattern': r'^AP-(\d+)-.*\.md$',
            'id_pattern': r'^AP-(\d+)$',
        },
    }


def parse_doc_id(doc_id: str) -> tuple[str, int]:
    """Parse document ID into type and number."""
    doc_id = doc_id.upper()

    for doc_type, config in get_doc_types().items():
        match = re.match(config['id_pattern'], doc_id)
        if match:
            return doc_type, int(match.group(1))

    raise ValueError(f"Invalid document ID: {doc_id}. Expected format: ADR-001, FDP-002, or AP-003")


def find_document(doc_type: str, number: int, project_dir: Path) -> Path | None:
    """Find a document by type and number."""
    config = get_doc_types()[doc_type]
    doc_dir = project_dir / config['dir']

    if not doc_dir.exists():
        return None

    pattern = re.compile(config['pattern'])

    for f in doc_dir.iterdir():
        if f.is_file():
            match = pattern.match(f.name)
            if match and int(match.group(1)) == number:
                return f

    return None


def update_status(filepath: Path, new_status: str = "Archived") -> str:
    """Update the Status section in a markdown document."""
    content = filepath.read_text()

    # Pattern to match the Status section
    # Handles: ## Status\n\nValue or ## Status\nValue
    status_pattern = r'(## Status\s*\n\s*\n?)([^\n#]+)'

    def replace_status(match):
        prefix = match.group(1)
        return f"{prefix}{new_status}"

    new_content, count = re.subn(status_pattern, replace_status, content)

    if count == 0:
        raise ValueError(f"Could not find Status section in {filepath}")

    # Add Archived date if not present
    if 'Archived' not in filepath.read_text() or new_status == "Archived":
        # Try to add after Status section
        archived_date = f"\n## Archived\n\n{date.today().isoformat()}\n"

        # Find position after Status section value
        status_match = re.search(r'## Status\s*\n\s*\n?[^\n#]+\n', new_content)
        if status_match:
            insert_pos = status_match.end()
            # Check if next section exists
            next_section = re.search(r'\n## ', new_content[insert_pos:])
            if next_section:
                # Insert before next section
                new_content = (
                    new_content[:insert_pos] +
                    archived_date +
                    new_content[insert_pos:]
                )

    return new_content


def archive_document(doc_id: str, project_dir: Path) -> Path:
    """Archive a planning document."""
    doc_type, number = parse_doc_id(doc_id)

    # Find the document
    filepath = find_document(doc_type, number, project_dir)
    if not filepath:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    # Check if already archived
    if 'archive' in str(filepath):
        raise ValueError(f"Document is already archived: {filepath}")

    # Update status
    new_content = update_status(filepath)
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
        help='Document ID (e.g., ADR-001, FDP-002, AP-003)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')),
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
