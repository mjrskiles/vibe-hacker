#!/usr/bin/env python3
"""
Archive a planning document.

Usage:
    archive.py <doc-id>
    archive.py --regenerate-index [--type TYPE] [--project-dir PATH]

Examples:
    archive.py ADR-001
    archive.py FDP-002
    archive.py AP-003
    archive.py RPT-001
    archive.py --regenerate-index              # rebuild all archive indexes
    archive.py --regenerate-index --type fdp   # rebuild just feature-designs

This will:
    1. Set the document's status to "archived" in frontmatter and body
    2. Leave a note under the title: the date, the status it had, and the
       sentence in planning.archive_note
    3. Move the file to the archive/ subdirectory
    4. Generate/update ARCHIVE.md index in the type directory
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from config import (
    ARCHIVE_DIR,
    find_document_by_id,
    get_all_types,
    get_archive_note,
    get_filename_pattern,
    get_id_prefix,
    get_planning_root,
    get_project_dir,
    get_type_config,
    id_examples,
    is_archived,
    parse_doc_id,
)
from frontmatter import document_status, insert_note_under_title, parse_frontmatter, set_status

ARCHIVED_STATUS = 'archived'


def archive_note(old_status: str | None) -> str:
    """Build the note left under an archived document's title."""
    was = f" (was {old_status.strip().lower()})" if old_status else ""
    return f"Archived {date.today().isoformat()}{was}. {get_archive_note()}"


def mark_archived(content: str) -> str:
    """Set a document's status to archived and leave the archive note in it."""
    old_status = document_status(content)
    try:
        content = set_status(content, ARCHIVED_STATUS, {'archived': date.today()})
    except ValueError:
        pass  # a document with no status still gets the note
    return insert_note_under_title(content, archive_note(old_status))



def regenerate_archive_index(type_dir: Path, doc_type: str) -> Path | None:
    """
    Regenerate ARCHIVE.md index from the archive/ subdirectory.

    Scans all .md files in archive/, reads their frontmatter, and writes
    a sorted index table to ARCHIVE.md in the parent type directory.

    Args:
        type_dir: The type directory (e.g., docs/planning/feature-designs/)
        doc_type: Document type key (adr, fdp, ap, report)

    Returns:
        Path to ARCHIVE.md, or None if no archive directory exists
    """
    archive_dir = type_dir / ARCHIVE_DIR
    if not archive_dir.exists():
        return None

    type_config = get_type_config(doc_type)
    type_name = type_config.get('name', doc_type.upper())
    id_format = type_config.get('id_format', '{number:03d}')

    # Filename patterns: the current convention, then the ID's letters as a
    # prefix (e.g., ADR-0001-...) for files named by an older convention
    patterns = [
        get_filename_pattern(doc_type),
        re.compile(rf'^{re.escape(get_id_prefix(doc_type))}-(\d+)-.*\.md$'),
    ]

    # Collect archived document info
    entries = []
    for f in sorted(archive_dir.iterdir()):
        if not f.is_file() or not f.name.endswith('.md'):
            continue

        number = None
        for pat in patterns:
            match = pat.match(f.name)
            if match:
                number = int(match.group(1))
                break
        if number is None:
            continue
        doc_id = id_format.format(number=number)

        # Read frontmatter for metadata
        try:
            content = f.read_text()
            frontmatter, body = parse_frontmatter(content)
        except Exception:
            frontmatter = None
            body = content if 'content' in dir() else ''

        # Extract title from body (first H1), strip any ID prefix like "ADR-001:" or "ADR-0001 —"
        title = ''
        title_match = re.search(r'^#\s+(.+)$', body or content, re.MULTILINE)
        if title_match:
            raw = title_match.group(1).strip()
            # Strip ID prefix patterns: "ADR-001: ", "FDP-0001 — ", "AP-002 - ", etc.
            title = re.sub(r'^[A-Z]+-\d+\s*[:\u2014\-]+\s*', '', raw).strip() or raw
        elif frontmatter and 'id' in frontmatter:
            title = f.stem

        # Extract status and archived date from frontmatter
        status = ''
        archived_date = ''
        if frontmatter:
            status = str(frontmatter.get('status', '')).title()
            archived_date = str(frontmatter.get('archived') or frontmatter.get('modified', ''))

        # Relative path from type_dir to archive file
        rel_path = f'{ARCHIVE_DIR}/{f.name}'

        entries.append({
            'number': number,
            'id': doc_id,
            'title': title,
            'status': status,
            'archived': archived_date,
            'rel_path': rel_path,
        })

    if not entries:
        # Remove stale index if archive is empty
        index_path = type_dir / 'ARCHIVE.md'
        if index_path.exists():
            index_path.unlink()
        return None

    # Sort by number
    entries.sort(key=lambda e: e['number'])

    # Build ARCHIVE.md
    lines = [
        f'# Archived {type_name}s',
        '',
        f'| ID | Title | Status | Archived | Path |',
        f'|----|-------|--------|----------|------|',
    ]

    for e in entries:
        link = f"[{e['rel_path']}]({e['rel_path']})"
        lines.append(f"| {e['id']} | {e['title']} | {e['status']} | {e['archived']} | {link} |")

    lines.append('')  # trailing newline

    index_path = type_dir / 'ARCHIVE.md'
    index_path.write_text('\n'.join(lines))

    return index_path


def archive_document(doc_id: str, project_dir: Path) -> Path:
    """Archive a planning document and regenerate the archive index."""
    doc_type, _ = parse_doc_id(doc_id)

    filepath = find_document_by_id(doc_id, project_dir)
    if is_archived(filepath):
        raise ValueError(f"Document is already archived: {filepath}")

    type_dir = filepath.parent
    archive_dir = type_dir / ARCHIVE_DIR
    new_path = archive_dir / filepath.name
    if new_path.exists():
        raise FileExistsError(f"Archive destination already exists: {new_path}")

    new_content = mark_archived(filepath.read_text())

    archive_dir.mkdir(exist_ok=True)
    new_path.write_text(new_content)
    filepath.unlink()

    # Regenerate archive index
    index_path = regenerate_archive_index(type_dir, doc_type)
    if index_path:
        print(f"Updated: {index_path}")

    return new_path


def main():
    parser = argparse.ArgumentParser(
        description='Archive a planning document.'
    )
    parser.add_argument(
        'doc_id',
        nargs='?',
        help=f'Document ID (e.g., {id_examples()})'
    )
    parser.add_argument(
        '--regenerate-index',
        action='store_true',
        help='Regenerate archive index without archiving a document'
    )
    parser.add_argument(
        '--type', '-t',
        choices=list(get_all_types().keys()),
        help='Document type to regenerate index for (with --regenerate-index)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    if args.regenerate_index:
        all_types = get_all_types()
        types_to_regen = [args.type] if args.type else list(all_types.keys())
        planning_root = args.project_dir / get_planning_root()

        for dtype in types_to_regen:
            type_config = all_types[dtype]
            type_dir = planning_root / type_config['dir']
            if not type_dir.exists():
                continue

            index_path = regenerate_archive_index(type_dir, dtype)
            if index_path:
                print(f"Regenerated: {index_path}")
            else:
                print(f"No archive found for {dtype}")

        sys.exit(0)

    if not args.doc_id:
        parser.error("doc_id is required (or use --regenerate-index)")

    try:
        new_path = archive_document(args.doc_id, args.project_dir)
        print(f"Archived: {new_path}")
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
