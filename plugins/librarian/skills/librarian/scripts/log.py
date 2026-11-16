#!/usr/bin/env python3
"""
Append a dated entry to a log.

A log is one append-only file per thread at <planning_root>/logs/<thread>.md,
for what was decided or observed, in the order it happened. Logs have no
number, status or frontmatter.

Usage:
    log.py <thread> "<title>" [--body "<content>"]

Examples:
    log.py davis "Step 6 listening" --body "Build: main a5c4f3d ..."
    log.py davis "Step 6 listening" --body - < notes.md    # body from stdin
"""

import argparse
import re
import sys
from pathlib import Path

from config import get_logs_dir, get_project_dir
from frontmatter import format_entry

THREAD_PATTERN = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
STDIN = '-'


def log_path(thread: str, project_dir: Path) -> Path:
    """
    Get the path of a thread's log.

    Raises:
        ValueError: If the thread name is not lowercase words joined by hyphens
    """
    if not THREAD_PATTERN.fullmatch(thread):
        raise ValueError(f"Invalid thread name: {thread!r}. Use lowercase letters, digits and hyphens.")
    return Path(project_dir) / get_logs_dir() / f"{thread}.md"


def append_entry(thread: str, title: str, body: str, project_dir: Path) -> Path:
    """
    Append an entry to a thread's log, creating the log if it does not exist.

    Returns:
        Path to the log
    """
    filepath = log_path(thread, project_dir)
    if filepath.exists():
        content = filepath.read_text().rstrip()
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        content = f"# {thread}: log"

    filepath.write_text(content + "\n\n" + format_entry(title, body))
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Append a dated entry to a log.'
    )
    parser.add_argument(
        'thread',
        help='Thread name, the log file\'s stem (e.g., davis)'
    )
    parser.add_argument(
        'title',
        help='Entry title'
    )
    parser.add_argument(
        '--body',
        default='',
        help='Entry body; "-" reads it from stdin (optional, can be added later by editing)'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=get_project_dir(),
        help='Project directory (default: CLAUDE_PROJECT_DIR or current dir)'
    )

    args = parser.parse_args()

    try:
        body = sys.stdin.read() if args.body == STDIN else args.body
        filepath = append_entry(args.thread, args.title, body or '[Add details here]', args.project_dir)
        print(f"Added entry to: {filepath}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
