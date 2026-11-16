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
import sys
from pathlib import Path

from config import (
    find_document_by_id,
    get_project_dir,
    get_type_config,
    id_examples,
    is_archived,
    is_retired,
    is_status_editable,
    parse_doc_id,
)
from frontmatter import document_status


def extract_status(filepath: Path) -> str:
    """Extract current status from a document (frontmatter or body)."""
    return document_status(filepath.read_text()) or 'Unknown'



def get_unlock_instruction(doc_type: str, status: str) -> str:
    """Get instruction for how to modify a locked document."""
    name = get_type_config(doc_type).get('name', doc_type.upper())
    instruction = f"A {name} with status '{status.lower()}' is read-only. Add an addendum"
    if is_retired(doc_type):
        return instruction + "."
    return instruction + ", or create a document that supersedes it."


def check_editable(doc_type: str, status: str, is_in_archive: bool) -> tuple[bool, str | None]:
    """
    Check if a document is editable.

    Returns:
        tuple of (is_editable, reason_if_locked)
    """
    if is_in_archive:
        return False, "Archived documents are read-only historical records. Add an addendum instead."

    if is_status_editable(doc_type, status):
        return True, None

    return False, get_unlock_instruction(doc_type, status)


def check_document_editable(doc_id: str, project_dir: Path, force: bool = False) -> tuple[Path, bool, str | None]:
    """
    Check if a document can be edited.

    Returns:
        tuple of (filepath, is_editable, message)
    """
    doc_type, _ = parse_doc_id(doc_id)
    filepath = find_document_by_id(doc_id, project_dir)

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
        help=f'Document ID (e.g., {id_examples()})'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force edit even if document is locked (use with caution)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
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
                print(f"\nTip: Use 'append.py {args.doc_id} \"<title>\"' to add an addendum instead.", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
