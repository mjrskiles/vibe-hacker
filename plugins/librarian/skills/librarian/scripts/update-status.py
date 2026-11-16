#!/usr/bin/env python3
"""
Update the status of a planning document.

Usage:
    update-status.py <doc-id> <new-status>

Examples:
    update-status.py ADR-001 accepted
    update-status.py FDP-002 "in progress"
    update-status.py AP-003 completed
    update-status.py RPT-001 published

Valid statuses are determined by each document type's configuration.
"""

import argparse
import sys
from pathlib import Path

from config import (
    find_document_by_id,
    get_project_dir,
    get_type_config,
    get_valid_statuses,
    id_examples,
    is_archive_trigger,
    is_archived,
    parse_doc_id,
)
from frontmatter import document_status, set_status


def validate_status(doc_type: str, new_status: str) -> str | None:
    """Validate status is valid for document type. Returns error message or None."""
    valid = get_valid_statuses(doc_type)
    normalized = new_status.lower().strip()

    if normalized not in [s.lower() for s in valid]:
        type_config = get_type_config(doc_type)
        type_name = type_config.get('name', doc_type.upper())
        return f"Invalid status '{new_status}' for {type_name}. Valid statuses: {', '.join(valid)}"

    return None


def update_document_status(doc_id: str, new_status: str, project_dir: Path) -> tuple[Path, str, bool]:
    """
    Update the status of a planning document.

    Returns:
        tuple of (filepath, old_status, should_archive)
    """
    doc_type, _ = parse_doc_id(doc_id)

    # Validate status
    error = validate_status(doc_type, new_status)
    if error:
        raise ValueError(error)

    filepath = find_document_by_id(doc_id, project_dir)
    if is_archived(filepath):
        raise ValueError(f"Cannot update archived document: {filepath}")

    content = filepath.read_text()
    old_status = document_status(content) or 'Unknown'
    filepath.write_text(set_status(content, new_status))

    # Check if should suggest archiving
    should_archive = is_archive_trigger(doc_type, new_status)

    return filepath, old_status, should_archive


def main():
    parser = argparse.ArgumentParser(
        description='Update the status of a planning document.'
    )
    parser.add_argument(
        'doc_id',
        help=f'Document ID (e.g., {id_examples()})'
    )
    parser.add_argument(
        'status',
        help='New status (e.g., accepted, "in progress", completed, published)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        filepath, old_status, should_archive = update_document_status(
            args.doc_id, args.status, args.project_dir
        )
        print(f"Updated: {filepath}")
        print(f"Status: {old_status} -> {args.status.lower()}")

        if should_archive:
            print(f"\nNote: This document is now {args.status.lower()}.")
            print(f"Consider archiving it with: python3 archive.py {args.doc_id}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
