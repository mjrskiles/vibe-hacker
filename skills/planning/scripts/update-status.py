#!/usr/bin/env python3
"""
Update the status of a planning document.

Usage:
    update-status.py <doc-id> <new-status>

Examples:
    update-status.py ADR-001 accepted
    update-status.py FDP-002 "in progress"
    update-status.py AP-003 completed

Valid statuses by document type:
    ADR: proposed, accepted, deprecated, superseded
    FDP: proposed, in progress, implemented, abandoned
    AP:  active, completed, abandoned
"""

import argparse
import os
import re
import sys
from pathlib import Path

from config import get_doc_dir


# Valid status transitions per document type
VALID_STATUSES = {
    'adr': ['proposed', 'accepted', 'deprecated', 'superseded'],
    'fdp': ['proposed', 'in progress', 'implemented', 'abandoned'],
    'ap': ['active', 'completed', 'abandoned'],
}

# Statuses that should trigger archiving suggestion
ARCHIVE_STATUSES = {
    'adr': ['deprecated', 'superseded'],
    'fdp': ['implemented', 'abandoned'],
    'ap': ['completed', 'abandoned'],
}


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


def extract_current_status(filepath: Path) -> str:
    """Extract current status from a markdown document."""
    content = filepath.read_text()
    match = re.search(r'## Status\s*\n\s*\n?([^\n#]+)', content)
    if match:
        return match.group(1).strip()
    return 'Unknown'


def update_status_in_file(filepath: Path, new_status: str) -> str:
    """Update the Status section in a markdown document."""
    content = filepath.read_text()

    # Pattern to match the Status section
    status_pattern = r'(## Status\s*\n\s*\n?)([^\n#]+)'

    def replace_status(match):
        prefix = match.group(1)
        # Capitalize first letter of each word for consistency
        formatted_status = new_status.title()
        return f"{prefix}{formatted_status}"

    new_content, count = re.subn(status_pattern, replace_status, content)

    if count == 0:
        raise ValueError(f"Could not find Status section in {filepath}")

    return new_content


def normalize_status(status: str) -> str:
    """Normalize status string for comparison."""
    return status.lower().strip()


def validate_status(doc_type: str, new_status: str) -> str | None:
    """Validate status is valid for document type. Returns error message or None."""
    valid = VALID_STATUSES.get(doc_type, [])
    normalized = normalize_status(new_status)

    if normalized not in [normalize_status(s) for s in valid]:
        return f"Invalid status '{new_status}' for {doc_type.upper()}. Valid statuses: {', '.join(valid)}"

    return None


def update_document_status(doc_id: str, new_status: str, project_dir: Path) -> tuple[Path, str, bool]:
    """
    Update the status of a planning document.

    Returns:
        tuple of (filepath, old_status, should_archive)
    """
    doc_type, number = parse_doc_id(doc_id)

    # Validate status
    error = validate_status(doc_type, new_status)
    if error:
        raise ValueError(error)

    # Find the document
    filepath = find_document(doc_type, number, project_dir)
    if not filepath:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    # Check if already archived
    if 'archive' in str(filepath):
        raise ValueError(f"Cannot update archived document: {filepath}")

    # Get current status
    old_status = extract_current_status(filepath)

    # Update status
    new_content = update_status_in_file(filepath, new_status)
    filepath.write_text(new_content)

    # Check if should suggest archiving
    should_archive = normalize_status(new_status) in [
        normalize_status(s) for s in ARCHIVE_STATUSES.get(doc_type, [])
    ]

    return filepath, old_status, should_archive


def main():
    parser = argparse.ArgumentParser(
        description='Update the status of a planning document.'
    )
    parser.add_argument(
        'doc_id',
        help='Document ID (e.g., ADR-001, FDP-002, AP-003)'
    )
    parser.add_argument(
        'status',
        help='New status (e.g., accepted, "in progress", completed)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        filepath, old_status, should_archive = update_document_status(
            args.doc_id, args.status, args.project_dir
        )
        print(f"Updated: {filepath}")
        print(f"Status: {old_status} -> {args.status.title()}")

        if should_archive:
            print(f"\nNote: This document is now {args.status.title()}.")
            print(f"Consider archiving it with: python3 archive.py {args.doc_id}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
