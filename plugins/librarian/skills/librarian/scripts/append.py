#!/usr/bin/env python3
"""
Append an addendum to a planning document.

Addenda can be added to any document regardless of status.
This allows locked/accepted documents to have clarifications
or updates added without modifying the original content.

Usage:
    append.py <doc-id> "<title>" [--body "<content>"]

Examples:
    append.py ADR-001 "Performance Clarification"
    append.py FDP-003 "Updated timeline" --body "Phase 1 delayed to Q2"
    append.py ADR-001 "Migration note" --body "Use pg_dump for best results"
"""

import argparse
import sys
from pathlib import Path

from config import find_document_by_id, get_project_dir, id_examples
from frontmatter import append_addendum


def main():
    parser = argparse.ArgumentParser(
        description='Append an addendum to a planning document.'
    )
    parser.add_argument(
        'doc_id',
        help=f'Document ID (e.g., {id_examples()})'
    )
    parser.add_argument(
        'title',
        help='Addendum title'
    )
    parser.add_argument(
        '--body',
        default='',
        help='Addendum body content (optional, can be added later by editing)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        filepath = find_document_by_id(args.doc_id, args.project_dir)

        # Use placeholder if no body provided
        body = args.body if args.body else '[Add details here]'

        filepath.write_text(append_addendum(filepath.read_text(), args.title, body))
        print(f"Added addendum to: {filepath}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
