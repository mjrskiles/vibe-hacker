#!/usr/bin/env python3
"""
Create a new planning document with auto-numbering.

Usage:
    new.py <type> "<title>"

Types:
    adr  - Architecture Decision Record
    fdp  - Feature Design Proposal
    ap   - Action Plan

Examples:
    new.py adr "Use PostgreSQL for persistence"
    new.py fdp "User Authentication System"
    new.py ap "Implement login flow"
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from string import Template

from config import get_doc_dir


def get_doc_types() -> dict:
    """Get document type configurations with paths from config."""
    return {
        'adr': {
            'dir': get_doc_dir('adr'),
            'pattern': r'^(\d{3})-.*\.md$',
            'prefix': '',
            'number_format': '{:03d}',
            'template': 'adr.md',
        },
        'fdp': {
            'dir': get_doc_dir('fdp'),
            'pattern': r'^FDP-(\d{3})-.*\.md$',
            'prefix': 'FDP-',
            'number_format': '{:03d}',
            'template': 'fdp.md',
        },
        'ap': {
            'dir': get_doc_dir('ap'),
            'pattern': r'^AP-(\d{3})-.*\.md$',
            'prefix': 'AP-',
            'number_format': '{:03d}',
            'template': 'action-plan.md',
        },
    }


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def find_next_number(doc_dir: Path, pattern: str) -> int:
    """Find the next available document number."""
    if not doc_dir.exists():
        return 1

    max_num = 0
    regex = re.compile(pattern)

    for f in doc_dir.iterdir():
        if f.is_file():
            match = regex.match(f.name)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    # Also check archive directory
    archive_dir = doc_dir / 'archive'
    if archive_dir.exists():
        for f in archive_dir.iterdir():
            if f.is_file():
                match = regex.match(f.name)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)

    return max_num + 1


def get_template_path(template_name: str) -> Path:
    """Get path to template file."""
    # Try relative to script location (plugin context)
    script_dir = Path(__file__).parent.parent / 'templates'
    template_path = script_dir / template_name

    if template_path.exists():
        return template_path

    # Try CLAUDE_PLUGIN_ROOT
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
    if plugin_root:
        template_path = Path(plugin_root) / 'skills' / 'planning' / 'templates' / template_name
        if template_path.exists():
            return template_path

    raise FileNotFoundError(f"Template not found: {template_name}")


def create_document(doc_type: str, title: str, project_dir: Path) -> Path:
    """Create a new planning document."""
    config = get_doc_types()[doc_type]

    doc_dir = project_dir / config['dir']
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Find next number
    next_num = find_next_number(doc_dir, config['pattern'])
    num_str = config['number_format'].format(next_num)

    # Create filename
    slug = slugify(title)
    filename = f"{config['prefix']}{num_str}-{slug}.md"
    filepath = doc_dir / filename

    # Check if file already exists
    if filepath.exists():
        raise FileExistsError(f"File already exists: {filepath}")

    # Read template
    template_path = get_template_path(config['template'])
    template_content = template_path.read_text()

    # Substitute variables
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
    parser = argparse.ArgumentParser(
        description='Create a new planning document with auto-numbering.'
    )
    parser.add_argument(
        'type',
        choices=['adr', 'fdp', 'ap'],
        help='Document type (adr, fdp, ap)'
    )
    parser.add_argument(
        'title',
        help='Document title'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        filepath = create_document(args.type, args.title, args.project_dir)
        print(f"Created: {filepath}")
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
