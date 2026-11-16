#!/usr/bin/env python3
"""
Create a new planning document with auto-numbering.

Usage:
    new.py <type> "<title>"

Types:
    adr    - Architecture Decision Record
    fdp    - Feature Design Proposal
    ap     - Action Plan
    report - Report

Examples:
    new.py adr "Use PostgreSQL for persistence"
    new.py fdp "User Authentication System"
    new.py ap "Implement login flow"
    new.py report "Q4 Performance Analysis"
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from string import Template

from config import (
    ARCHIVE_DIR,
    format_filename,
    get_all_types,
    get_doc_dir,
    get_filename_pattern,
    get_project_dir,
    get_template_path,
    get_type_config,
    is_retired,
)


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def find_next_number(doc_dir: Path, pattern: re.Pattern) -> int:
    """Find the next available document number, counting archived documents."""
    max_num = 0
    for directory in (doc_dir, doc_dir / ARCHIVE_DIR):
        if not directory.is_dir():
            continue
        for f in directory.iterdir():
            match = pattern.match(f.name) if f.is_file() else None
            if match:
                max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def load_template(doc_type: str, project_dir: Path) -> str:
    """Load template content for a document type."""
    template_path = get_template_path(doc_type, project_dir)
    if template_path is None:
        raise FileNotFoundError(f"Template not found for type: {doc_type}")
    return template_path.read_text()


def create_document(doc_type: str, title: str, project_dir: Path) -> Path:
    """
    Create a new planning document.

    Raises:
        ValueError: If the type is retired or the title has no usable characters
        FileExistsError: If the document's file already exists
        FileNotFoundError: If the type has no template
    """
    if is_retired(doc_type):
        name = get_type_config(doc_type).get('name', doc_type.upper())
        raise ValueError(
            f"{name} is a retired document type (planning.retired): "
            "new documents of this type are not created."
        )

    slug = slugify(title)
    if not slug:
        raise ValueError(f"Title has no characters usable in a filename: {title!r}")

    doc_dir = project_dir / get_doc_dir(doc_type)
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Find next number
    next_num = find_next_number(doc_dir, get_filename_pattern(doc_type))

    # Create filename using config format
    filename = format_filename(doc_type, next_num, slug)
    filepath = doc_dir / filename

    # Check if file already exists
    if filepath.exists():
        raise FileExistsError(f"File already exists: {filepath}")

    # Read template
    template_content = load_template(doc_type, project_dir)

    # Substitute variables
    # NUMBER is zero-padded for display in document
    num_str = f"{next_num:03d}"

    template = Template(template_content)
    content = template.safe_substitute(
        NUMBER=num_str,
        TITLE=title,
        DATE=date.today().isoformat(),
    )

    # Write file
    filepath.write_text(content)

    return filepath


def main():
    # Get available types from config
    all_types = get_all_types()
    type_choices = list(all_types.keys())

    parser = argparse.ArgumentParser(
        description='Create a new planning document with auto-numbering.'
    )
    parser.add_argument(
        'type',
        choices=type_choices,
        help=f'Document type ({", ".join(type_choices)})'
    )
    parser.add_argument(
        'title',
        help='Document title'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        filepath = create_document(args.type, args.title, args.project_dir)
        print(f"Created: {filepath}")
    except (FileExistsError, FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
