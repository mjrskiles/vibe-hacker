#!/usr/bin/env python3
"""
Validate and enable editing of a planning document.

This script checks if a document can be edited based on its status and type,
then outputs the file path for editing if allowed.

Usage:
    edit.py <doc-id> [--force]

Examples:
    edit.py ADR-001        # Check if editable, output path
    edit.py FDP-002        # Check if editable, output path
    edit.py ADR-001 --force  # Force edit even if locked (outputs warning)

Exit codes:
    0 - Document is editable, path printed to stdout
    1 - Document cannot be edited (locked status or archived)
    2 - Document not found or other error
"""

import argparse
import os
import re
import sys
from pathlib import Path

from config import get_doc_dir


# Statuses that lock a document from editing
LOCKED_STATUSES = {
    'adr': ['accepted', 'deprecated', 'superseded', 'archived'],
    'fdp': ['implemented', 'abandoned', 'archived'],
    'ap': ['completed', 'abandoned', 'archived'],
}

# Instructions for editing locked documents
UNLOCK_INSTRUCTIONS = {
    'adr': {
        'accepted': "To modify an accepted ADR, create a new ADR that supersedes it.",
        'deprecated': "Deprecated ADRs are read-only. Create a new ADR if needed.",
        'superseded': "Superseded ADRs are read-only. Edit the superseding ADR instead.",
        'archived': "Archived documents are read-only historical records.",
    },
    'fdp': {
        'implemented': "Implemented FDPs are read-only. Create a new FDP for changes.",
        'abandoned': "Abandoned FDPs are read-only. Create a new FDP to revisit.",
        'archived': "Archived documents are read-only historical records.",
    },
    'ap': {
        'completed': "Completed action plans are read-only. Create a new AP for follow-up work.",
        'abandoned': "Abandoned action plans are read-only. Create a new AP to revisit.",
        'archived': "Archived documents are read-only historical records.",
    },
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


def find_document(doc_type: str, number: int, project_dir: Path, include_archive: bool = True) -> Path | None:
    """Find a document by type and number."""
    config = get_doc_types()[doc_type]
    doc_dir = project_dir / config['dir']

    if not doc_dir.exists():
        return None

    pattern = re.compile(config['pattern'])

    # Check main directory first
    for f in doc_dir.iterdir():
        if f.is_file():
            match = pattern.match(f.name)
            if match and int(match.group(1)) == number:
                return f

    # Check archive if requested
    if include_archive:
        archive_dir = doc_dir / 'archive'
        if archive_dir.exists():
            for f in archive_dir.iterdir():
                if f.is_file():
                    match = pattern.match(f.name)
                    if match and int(match.group(1)) == number:
                        return f

    return None


def extract_status(filepath: Path) -> str:
    """Extract current status from a markdown document."""
    content = filepath.read_text()
    match = re.search(r'## Status\s*\n\s*\n?([^\n#]+)', content)
    if match:
        return match.group(1).strip()
    return 'Unknown'


def normalize_status(status: str) -> str:
    """Normalize status string for comparison."""
    return status.lower().strip()


def is_archived(filepath: Path) -> bool:
    """Check if document is in archive directory."""
    return 'archive' in filepath.parts


def check_editable(doc_type: str, status: str, is_in_archive: bool) -> tuple[bool, str | None]:
    """
    Check if a document is editable.

    Returns:
        tuple of (is_editable, reason_if_locked)
    """
    if is_in_archive:
        return False, UNLOCK_INSTRUCTIONS[doc_type].get('archived', "Archived documents are read-only.")

    normalized = normalize_status(status)
    locked = [normalize_status(s) for s in LOCKED_STATUSES.get(doc_type, [])]

    if normalized in locked:
        instructions = UNLOCK_INSTRUCTIONS.get(doc_type, {})
        # Find matching instruction
        for locked_status, instruction in instructions.items():
            if normalize_status(locked_status) == normalized:
                return False, instruction
        return False, f"Document with status '{status}' is locked."

    return True, None


def check_document_editable(doc_id: str, project_dir: Path, force: bool = False) -> tuple[Path, bool, str | None]:
    """
    Check if a document can be edited.

    Returns:
        tuple of (filepath, is_editable, message)
    """
    doc_type, number = parse_doc_id(doc_id)

    # Find the document
    filepath = find_document(doc_type, number, project_dir)
    if not filepath:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    # Get status and check if editable
    status = extract_status(filepath)
    in_archive = is_archived(filepath)

    is_editable, reason = check_editable(doc_type, status, in_archive)

    if not is_editable and force:
        return filepath, True, f"WARNING: Forcing edit of locked document. {reason}"

    if not is_editable:
        return filepath, False, reason

    return filepath, True, None


def main():
    parser = argparse.ArgumentParser(
        description='Check if a planning document can be edited and output its path.'
    )
    parser.add_argument(
        'doc_id',
        help='Document ID (e.g., ADR-001, FDP-002, AP-003)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force edit even if document is locked (use with caution)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only output the file path, no status messages'
    )

    args = parser.parse_args()

    try:
        filepath, is_editable, message = check_document_editable(
            args.doc_id, args.project_dir, args.force
        )

        if is_editable:
            if message and not args.quiet:
                print(message, file=sys.stderr)
            print(filepath)
            sys.exit(0)
        else:
            if not args.quiet:
                print(f"Error: Cannot edit {args.doc_id}", file=sys.stderr)
                print(f"Status: {extract_status(filepath)}", file=sys.stderr)
                if message:
                    print(f"\n{message}", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
