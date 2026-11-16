"""
Shared configuration for planning scripts.

Reads planning configuration from vibe-hacker.json.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

# Default planning root if not configured
DEFAULT_PLANNING_ROOT = 'docs/planning'

# Directories under the planning root, or under a type's directory
ARCHIVE_DIR = 'archive'
LOGS_DIR = 'logs'
TEMPLATES_DIR = 'templates'

# Templates shipped with the skill
BUILTIN_TEMPLATES = Path(__file__).resolve().parent.parent / 'templates'

# Closing sentence of the note archive.py leaves in a document
DEFAULT_ARCHIVE_NOTE = 'A historical record.'

# Default type definitions (v0.2.0 format)
DEFAULT_TYPES = {
    'adr': {
        'name': 'Architecture Decision Record',
        'dir': 'decisions',
        'prefix': '',
        'filename_format': '{number:03d}-{slug}.md',
        'id_format': 'ADR-{number:03d}',
        'template': 'adr.md',
        'statuses': {
            'initial': 'proposed',
            'editable': ['proposed'],
            'final': ['accepted'],
            'archive_triggers': ['deprecated', 'superseded']
        }
    },
    'fdp': {
        'name': 'Feature Design Proposal',
        'dir': 'designs',
        'prefix': 'FDP-',
        'filename_format': 'FDP-{number:03d}-{slug}.md',
        'id_format': 'FDP-{number:03d}',
        'template': 'fdp.md',
        'statuses': {
            'initial': 'proposed',
            'editable': ['proposed', 'in progress'],
            'final': ['implemented'],
            'archive_triggers': ['implemented', 'abandoned']
        }
    },
    'ap': {
        'name': 'Action Plan',
        'dir': 'action-plans',
        'prefix': 'AP-',
        'filename_format': 'AP-{number:03d}-{slug}.md',
        'id_format': 'AP-{number:03d}',
        'template': 'action-plan.md',
        'statuses': {
            'initial': 'active',
            'editable': ['active'],
            'final': ['completed'],
            'archive_triggers': ['completed', 'abandoned']
        }
    },
    'report': {
        'name': 'Report',
        'dir': 'reports',
        'prefix': 'RPT-',
        'filename_format': 'RPT-{number:03d}-{slug}.md',
        'id_format': 'RPT-{number:03d}',
        'template': 'report.md',
        'statuses': {
            'initial': 'draft',
            'editable': ['draft'],
            'final': ['published'],
            'archive_triggers': ['superseded', 'obsoleted']
        }
    }
}


def get_project_dir() -> Path:
    """Get the project directory."""
    return Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))


def _get_git_root(project_dir: Path) -> Optional[Path]:
    """Get the git root for the given directory, or None if not in a repo."""
    try:
        result = subprocess.run(
            ['git', '-C', str(project_dir), 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_config_path() -> Path:
    """Get path to vibe-hacker.json config file.

    Resolution order (multi-repo aware):
      1. CLAUDE_PROJECT_DIR (authoritative workspace root when set)
      2. Git root (standalone repo fallback, prevents parent leakage)
      3. Current directory (last resort)
    """
    project_dir = get_project_dir()

    # CLAUDE_PROJECT_DIR is authoritative — it's the workspace root
    workspace_config = project_dir / '.claude' / 'vibe-hacker.json'
    if workspace_config.exists():
        return workspace_config

    # Fall back to git root (prevents parent-repo leakage for standalone use)
    git_root = _get_git_root(project_dir)
    if git_root:
        git_config = git_root / '.claude' / 'vibe-hacker.json'
        if git_config.exists():
            return git_config

    # Last resort
    return workspace_config


def load_config() -> dict:
    """Load configuration from vibe-hacker.json."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to vibe-hacker.json."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + '\n')


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


def get_type_config(doc_type: str) -> dict:
    """
    Get the full configuration for a document type.

    Args:
        doc_type: Document type key (adr, fdp, ap, report)

    Returns:
        Type configuration dictionary
    """
    config = load_config()
    planning_config = config.get('planning', {})
    subdirs = planning_config.get('subdirs', {})

    default = DEFAULT_TYPES.get(doc_type, {}).copy()

    # Override dir from subdirs config if present
    if doc_type in subdirs:
        default['dir'] = subdirs[doc_type]

    return default


def get_all_types() -> dict:
    """
    Get configuration for all document types.

    Returns:
        Dictionary mapping type keys to their configurations
    """
    config = load_config()
    planning_config = config.get('planning', {})
    subdirs = planning_config.get('subdirs', {})

    # Start with defaults
    types = {k: v.copy() for k, v in DEFAULT_TYPES.items()}

    # Apply subdirs overrides
    for type_key, subdir in subdirs.items():
        if type_key in types:
            types[type_key]['dir'] = subdir

    return types


def get_doc_dir(doc_type: str) -> str:
    """Get the directory path for a document type."""
    planning_root = get_planning_root()
    type_config = get_type_config(doc_type)
    return f"{planning_root}/{type_config['dir']}"


def get_planning_subdirs() -> dict:
    """Get subdirectory names for each document type."""
    types = get_all_types()
    return {key: cfg['dir'] for key, cfg in types.items()}


def is_status_editable(doc_type: str, status: str) -> bool:
    """
    Check if a document with given status can be edited.

    Args:
        doc_type: Document type key
        status: Current status (case-insensitive)

    Returns:
        True if document can be edited
    """
    type_config = get_type_config(doc_type)
    statuses = type_config.get('statuses', {})
    editable = statuses.get('editable', [])
    return status.lower() in [s.lower() for s in editable]


def is_archive_trigger(doc_type: str, status: str) -> bool:
    """
    Check if a status should trigger an archive suggestion.

    Args:
        doc_type: Document type key
        status: Current status (case-insensitive)

    Returns:
        True if status suggests archiving
    """
    type_config = get_type_config(doc_type)
    statuses = type_config.get('statuses', {})
    triggers = statuses.get('archive_triggers', [])
    return status.lower() in [s.lower() for s in triggers]


def get_valid_statuses(doc_type: str) -> list:
    """
    Get all valid statuses for a document type.

    Args:
        doc_type: Document type key

    Returns:
        List of valid status strings
    """
    type_config = get_type_config(doc_type)
    statuses = type_config.get('statuses', {})

    all_statuses = set()
    all_statuses.add(statuses.get('initial', ''))
    all_statuses.update(statuses.get('editable', []))
    all_statuses.update(statuses.get('final', []))
    all_statuses.update(statuses.get('archive_triggers', []))
    all_statuses.discard('')

    return sorted(all_statuses)


def format_doc_id(doc_type: str, number: int) -> str:
    """
    Format a document ID using the type's id_format.

    Args:
        doc_type: Document type key
        number: Document number

    Returns:
        Formatted ID string (e.g., "ADR-001")
    """
    type_config = get_type_config(doc_type)
    id_format = type_config.get('id_format', '{number:03d}')
    return id_format.format(number=number)


def format_filename(doc_type: str, number: int, slug: str) -> str:
    """
    Format a document filename using the type's filename_format.

    Args:
        doc_type: Document type key
        number: Document number
        slug: URL-friendly title slug

    Returns:
        Formatted filename (e.g., "001-my-title.md")
    """
    type_config = get_type_config(doc_type)
    filename_format = type_config.get('filename_format', '{number:03d}-{slug}.md')
    return filename_format.format(number=number, slug=slug)


def find_template(template_name: str, project_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find a template by file name.

    A template in <planning root>/templates/ of the project takes precedence
    over the one shipped with the skill.

    Args:
        template_name: Template file name (e.g., "fdp.md")
        project_dir: Project directory (default: get_project_dir())

    Returns:
        Path to the template file or None if not found
    """
    project_dir = Path(project_dir) if project_dir is not None else get_project_dir()
    candidates = [
        project_dir / get_planning_root() / TEMPLATES_DIR / template_name,
        BUILTIN_TEMPLATES / template_name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def get_template_path(doc_type: str, project_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Get the path to a document type's template.

    Args:
        doc_type: Document type key
        project_dir: Project directory (default: get_project_dir())

    Returns:
        Path to template file or None if not found
    """
    template_name = get_type_config(doc_type).get('template')
    if not template_name:
        return None
    return find_template(template_name, project_dir)


def get_id_prefix(doc_type: str) -> str:
    """Get the letters of a type's document ID (e.g., "ADR" for "ADR-001")."""
    return DEFAULT_TYPES[doc_type]['id_format'].split('-', 1)[0]


def id_examples() -> str:
    """List one example ID per document type, for help and error text."""
    return ', '.join(format_doc_id(doc_type, 1) for doc_type in DEFAULT_TYPES)


def parse_doc_id(doc_id: str) -> tuple[str, int]:
    """
    Parse a document ID into type and number.

    Args:
        doc_id: Document ID like "ADR-001" (case-insensitive)

    Returns:
        Tuple of (doc_type, number)

    Raises:
        ValueError: If the ID matches no document type
    """
    match = re.fullmatch(r'([A-Z]+)-(\d+)', doc_id.strip().upper())
    if match:
        for doc_type in DEFAULT_TYPES:
            if get_id_prefix(doc_type) == match.group(1):
                return doc_type, int(match.group(2))
    raise ValueError(f"Invalid document ID: {doc_id}. Expected a form like: {id_examples()}")


def get_filename_pattern(doc_type: str) -> re.Pattern:
    """
    Get the pattern a type's filenames follow.

    Group 1 is the document number, group 2 the slug.
    """
    prefix = get_type_config(doc_type).get('prefix', '')
    return re.compile(rf'^{re.escape(prefix)}(\d+)-(.*)\.md$')


def is_archived(filepath: Path) -> bool:
    """Check whether a document sits in an archive directory."""
    return Path(filepath).parent.name == ARCHIVE_DIR


def find_document(doc_type: str, number: int, project_dir: Path,
                  search_archive: bool = True) -> Optional[Path]:
    """
    Find a document by type and number.

    Args:
        doc_type: Document type key
        number: Document number
        project_dir: Project directory
        search_archive: Also look in the type's archive directory

    Returns:
        Path to the document, the live one first, or None if not found
    """
    doc_dir = Path(project_dir) / get_doc_dir(doc_type)
    pattern = get_filename_pattern(doc_type)
    directories = [doc_dir, doc_dir / ARCHIVE_DIR] if search_archive else [doc_dir]

    for directory in directories:
        if not directory.is_dir():
            continue
        for f in sorted(directory.iterdir()):
            match = pattern.match(f.name) if f.is_file() else None
            if match and int(match.group(1)) == number:
                return f
    return None


def find_document_by_id(doc_id: str, project_dir: Path, search_archive: bool = True) -> Path:
    """
    Find a document by its ID.

    Raises:
        ValueError: If the ID matches no document type
        FileNotFoundError: If no such document exists
    """
    doc_type, number = parse_doc_id(doc_id)
    filepath = find_document(doc_type, number, project_dir, search_archive)
    if filepath is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")
    return filepath


def get_retired_types() -> list:
    """Get the document types that can no longer be created (planning.retired)."""
    retired = load_config().get('planning', {}).get('retired', [])
    return [str(doc_type).lower() for doc_type in retired]


def is_retired(doc_type: str) -> bool:
    """Check whether new documents of a type are refused."""
    return doc_type.lower() in get_retired_types()


def get_archive_note() -> str:
    """Get the closing sentence of the archive note (planning.archive_note)."""
    return load_config().get('planning', {}).get('archive_note') or DEFAULT_ARCHIVE_NOTE


def get_logs_dir() -> str:
    """Get the directory path for logs."""
    return f"{get_planning_root()}/{LOGS_DIR}"
