#!/usr/bin/env python3
"""
Review planning documents that need attention.

Two lists: open documents (everything not in a terminal state), and finished
documents that are still live (status is one the type archives on).

Usage:
    review.py [--type TYPE] [--project-dir PATH]

Examples:
    review.py                     # Review all open documents
    review.py --type fdp          # Review open FDPs only
    review.py --project-dir /path/to/sbl-apps  # Review app-level plans
"""

import argparse
import re
import sys
from pathlib import Path

from config import (
    get_all_types,
    get_filename_pattern,
    get_planning_root,
    get_project_dir,
    get_type_config,
    is_archive_trigger,
    is_retired,
)
from frontmatter import parse_frontmatter, extract_status_from_body, extract_title_from_body


def get_terminal_statuses(doc_type: str) -> set[str]:
    """Get all terminal statuses for a document type."""
    type_config = get_type_config(doc_type)
    statuses = type_config.get('statuses', {})
    terminal = set()
    for s in statuses.get('final', []):
        terminal.add(s.lower())
    for s in statuses.get('archive_triggers', []):
        terminal.add(s.lower())
    return terminal


def extract_summary(filepath: Path) -> str:
    """Extract a brief summary from a document.

    Looks for the first non-empty paragraph after the H1 heading and any
    Status section.  If content starts with a subheading, looks under it.
    Falls back to '(no summary)'.
    """
    try:
        content = filepath.read_text()
        frontmatter, body = parse_frontmatter(content)
        text = (body if frontmatter else content).lstrip('\n')

        # Skip H1 heading
        text = re.sub(r'^#\s+[^\n]+\n*', '', text, count=1)

        # Skip the ## Status section, up to the next heading
        text = re.sub(r'^## Status[ \t]*\n.*?(?=^#|\Z)', '', text, count=1, flags=re.DOTALL | re.MULTILINE)

        # Skip blank lines
        text = text.lstrip('\n')

        # If we're at a subheading (## Summary, ## Context, etc.), skip it
        text = re.sub(r'^#{2,}\s+[^\n]+\n*', '', text, count=1)
        text = text.lstrip('\n')

        # Take first non-empty paragraph (up to blank line or next heading)
        match = re.match(r'([^\n#][^\n]*(?:\n(?![\n#])[^\n]+)*)', text)
        if match:
            summary = match.group(1).strip()
            # Truncate long summaries
            if len(summary) > 120:
                summary = summary[:117] + '...'
            return summary

        return '(no summary)'
    except Exception:
        return '(error reading file)'


def extract_status(filepath: Path) -> str:
    """Extract status from a document."""
    try:
        content = filepath.read_text()
        frontmatter, body = parse_frontmatter(content)
        if frontmatter and 'status' in frontmatter:
            status = frontmatter['status']
            return status.title() if isinstance(status, str) else str(status)
        status = extract_status_from_body(content)
        return status if status else 'Unknown'
    except Exception:
        return 'Error'


def extract_title(filepath: Path) -> str:
    """Extract title from a document."""
    try:
        content = filepath.read_text()
        frontmatter, body = parse_frontmatter(content)
        title = extract_title_from_body(body if frontmatter else content)
        return title if title else filepath.stem
    except Exception:
        return filepath.stem


def extract_modified(filepath: Path) -> str:
    """Extract modified date from frontmatter."""
    try:
        content = filepath.read_text()
        frontmatter, _ = parse_frontmatter(content)
        if frontmatter:
            return str(frontmatter.get('modified', frontmatter.get('created', '?')))
        return '?'
    except Exception:
        return '?'


def find_docs(project_dir: Path, doc_type: str | None = None) -> tuple[list[dict], list[dict]]:
    """
    Find the live documents that need attention.

    Returns:
        Tuple of (open documents, finished documents not yet archived)
    """
    open_docs, unarchived = [], []
    all_types = get_all_types()
    types_to_check = [doc_type] if doc_type else list(all_types.keys())

    planning_root = project_dir / get_planning_root()

    for dtype in types_to_check:
        type_config = all_types.get(dtype)
        if not type_config:
            continue

        doc_dir = planning_root / type_config['dir']
        if not doc_dir.exists():
            continue

        terminal = get_terminal_statuses(dtype)
        pattern = get_filename_pattern(dtype)
        id_format = type_config.get('id_format', '{number:03d}')

        for f in sorted(doc_dir.iterdir()):
            match = pattern.match(f.name) if f.is_file() else None
            if not match:
                continue

            status = extract_status(f)
            archivable = is_archive_trigger(dtype, status)
            if status.lower() in terminal and not archivable:
                continue

            (unarchived if archivable else open_docs).append({
                'id': id_format.format(number=int(match.group(1))),
                'type': dtype.upper() + (' (retired type)' if is_retired(dtype) else ''),
                'status': status,
                'title': extract_title(f),
                'summary': extract_summary(f),
                'modified': extract_modified(f),
                'path': str(f.relative_to(project_dir)),
            })

    return open_docs, unarchived


def format_review(open_docs: list[dict], unarchived: list[dict]) -> str:
    """Format the two lists as a review summary."""
    if not open_docs and not unarchived:
        return "All clear: no open planning documents, none waiting to be archived."

    lines = [f"Open planning documents: {len(open_docs)} total\n"]

    by_type: dict[str, list[dict]] = {}
    for doc in open_docs:
        by_type.setdefault(doc['type'], []).append(doc)

    for doc_type, docs in by_type.items():
        lines.append(f"## {doc_type} ({len(docs)})\n")

        for doc in docs:
            title = doc['title']
            if len(title) > 60:
                title = title[:57] + '...'

            lines.append(f"  {doc['id']}  [{doc['status']}]  {title}")
            lines.append(f"           modified: {doc['modified']}  path: {doc['path']}")
            lines.append(f"           {doc['summary']}")
            lines.append('')

    if unarchived:
        lines.append(f"Finished, not archived: {len(unarchived)} total\n")
        for doc in unarchived:
            title = doc['title']
            if len(title) > 60:
                title = title[:57] + '...'
            lines.append(f"  {doc['id']}  [{doc['status']}]  {title}")
        lines.append('')

    return '\n'.join(lines)


def main():
    all_types = get_all_types()
    type_choices = list(all_types.keys())

    parser = argparse.ArgumentParser(
        description='Review planning documents that are open, or finished and not yet archived.'
    )
    parser.add_argument(
        '--type', '-t',
        choices=type_choices,
        help=f'Filter by document type ({", ".join(type_choices)})'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()
    print(format_review(*find_docs(args.project_dir, doc_type=args.type)))


if __name__ == '__main__':
    main()
