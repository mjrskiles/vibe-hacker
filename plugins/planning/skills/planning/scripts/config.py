"""
Shared configuration for planning scripts.

Reads planning configuration from vibe-hacker.json.
"""

import json
import os
from pathlib import Path

# Default planning root if not configured
DEFAULT_PLANNING_ROOT = 'docs/planning'

# Default subdirectories
DEFAULT_SUBDIRS = {
    'adr': 'decision-records',
    'fdp': 'feature-designs',
    'ap': 'action-plans',
}


def get_project_dir() -> Path:
    """Get the project directory."""
    return Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))


def get_config_path() -> Path:
    """Get path to vibe-hacker.json config file."""
    return get_project_dir() / '.claude' / 'vibe-hacker.json'


def load_config() -> dict:
    """Load configuration from vibe-hacker.json."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def get_planning_root() -> str:
    """Get the planning root directory from config."""
    config = load_config()

    # Check protected_paths.planning_root first (as shown in FDP-002)
    planning_root = config.get('protected_paths', {}).get('planning_root')
    if planning_root:
        return planning_root

    # Check top-level planning.root
    planning_root = config.get('planning', {}).get('root')
    if planning_root:
        return planning_root

    return DEFAULT_PLANNING_ROOT


def get_planning_subdirs() -> dict:
    """Get subdirectory names for each document type."""
    config = load_config()

    # Allow overriding subdirectory names
    subdirs = config.get('planning', {}).get('subdirs', {})

    return {
        'adr': subdirs.get('adr', DEFAULT_SUBDIRS['adr']),
        'fdp': subdirs.get('fdp', DEFAULT_SUBDIRS['fdp']),
        'ap': subdirs.get('ap', DEFAULT_SUBDIRS['ap']),
    }


def get_doc_dir(doc_type: str) -> str:
    """Get the directory path for a document type."""
    planning_root = get_planning_root()
    subdirs = get_planning_subdirs()
    subdir = subdirs.get(doc_type, doc_type)
    return f"{planning_root}/{subdir}"
