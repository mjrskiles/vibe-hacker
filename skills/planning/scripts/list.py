#!/usr/bin/env python3
"""
List planning documents.

Usage:
    list.py [--type TYPE] [--status STATUS] [--include-archived]

Examples:
    list.py                     # List all active documents
    list.py --type adr          # List only ADRs
    list.py --status proposed   # List documents with Proposed status
    list.py --include-archived  # Include archived documents
"""

import argparse
import os
import re
import sys
from pathlib import Path

from config import get_doc_dir


def get_doc_types() -> dict:
    """Get document type configurations with paths from config."""
    return {
        'adr': {
            'dir': get_doc_dir('adr'),
            'pattern': r'^(\d+)-(.*)\.md$',
            'id_format': 'ADR-{:03d}',
            'label': 'ADR',
        },
        'fdp': {
            'dir': get_doc_dir('fdp'),
            'pattern': r'^FDP-(\d+)-(.*)\.md$',
            'id_format': 'FDP-{:03d}',
            'label': 'FDP',
        },
        'ap': {
            'dir': get_doc_dir('ap'),
            'pattern': r'^AP-(\d+)-(.*)\.md$',
            'id_format': 'AP-{:03d}',
            'label': 'Action Plan',
        },
    }


def extract_status(filepath: Path) -> str:
    """Extract status from a markdown document."""
    try:
        content = filepath.read_text()
        # Look for ## Status section
        match = re.search(r'## Status\s*\n\s*\n?([^\n#]+)', content)
        if match:
            status = match.group(1).strip()
            # Clean up status (remove markdown links, etc.)
            status = re.sub(r'\[.*?\]\(.*?\)', '', status).strip()
            # Take first word/phrase before any pipe or other separator
            status = status.split('|')[0].strip()
            return status
        return 'Unknown'
    except Exception:
        return 'Error'


def extract_title(filepath: Path) -> str:
    """Extract title from markdown document."""
    try:
        content = filepath.read_text()
        # Look for first H1 heading
        match = re.search(r'^# .+?:\s*(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Fallback: first H1
        match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return filepath.stem
    except Exception:
        return filepath.stem


def list_documents(
    project_dir: Path,
    doc_type: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
) -> list[dict]:
    """List planning documents."""
    documents = []

    doc_types = get_doc_types()
    types_to_check = [doc_type] if doc_type else list(doc_types.keys())

    for dtype in types_to_check:
        config = doc_types[dtype]
        doc_dir = project_dir / config['dir']

        if not doc_dir.exists():
            continue

        pattern = re.compile(config['pattern'])

        # Check main directory
        for f in sorted(doc_dir.iterdir()):
            if not f.is_file():
                continue

            match = pattern.match(f.name)
            if not match:
                continue

            number = int(match.group(1))
            status = extract_status(f)
            title = extract_title(f)

            doc_info = {
                'id': config['id_format'].format(number),
                'type': config['label'],
                'title': title,
                'status': status,
                'path': str(f.relative_to(project_dir)),
                'archived': False,
            }

            if status_filter and status.lower() != status_filter.lower():
                continue

            documents.append(doc_info)

        # Check archive directory
        if include_archived:
            archive_dir = doc_dir / 'archive'
            if archive_dir.exists():
                for f in sorted(archive_dir.iterdir()):
                    if not f.is_file():
                        continue

                    match = pattern.match(f.name)
                    if not match:
                        continue

                    number = int(match.group(1))
                    status = extract_status(f)
                    title = extract_title(f)

                    doc_info = {
                        'id': config['id_format'].format(number),
                        'type': config['label'],
                        'title': title,
                        'status': status,
                        'path': str(f.relative_to(project_dir)),
                        'archived': True,
                    }

                    if status_filter and status.lower() != status_filter.lower():
                        continue

                    documents.append(doc_info)

    return documents


def format_table(documents: list[dict]) -> str:
    """Format documents as a table."""
    if not documents:
        return "No documents found."

    # Calculate column widths
    headers = ['ID', 'Type', 'Status', 'Title']
    widths = [len(h) for h in headers]

    for doc in documents:
        widths[0] = max(widths[0], len(doc['id']))
        widths[1] = max(widths[1], len(doc['type']))
        widths[2] = max(widths[2], len(doc['status']) + (4 if doc['archived'] else 0))
        widths[3] = max(widths[3], min(len(doc['title']), 50))

    # Format header
    header_fmt = ' | '.join(f"{{:<{w}}}" for w in widths)
    separator = '-+-'.join('-' * w for w in widths)

    lines = [
        header_fmt.format(*headers),
        separator,
    ]

    # Format rows
    for doc in documents:
        status = doc['status']
        if doc['archived']:
            status = f"[A] {status}"

        title = doc['title']
        if len(title) > 50:
            title = title[:47] + '...'

        lines.append(header_fmt.format(
            doc['id'],
            doc['type'],
            status,
            title,
        ))

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='List planning documents.'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['adr', 'fdp', 'ap'],
        help='Filter by document type'
    )
    parser.add_argument(
        '--status', '-s',
        help='Filter by status (e.g., proposed, accepted, active)'
    )
    parser.add_argument(
        '--include-archived', '-a',
        action='store_true',
        help='Include archived documents'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    documents = list_documents(
        args.project_dir,
        doc_type=args.type,
        status_filter=args.status,
        include_archived=args.include_archived,
    )

    print(format_table(documents))


if __name__ == '__main__':
    main()
