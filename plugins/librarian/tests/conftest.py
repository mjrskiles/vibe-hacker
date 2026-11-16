"""Fixtures for the librarian's tests: a throwaway project and a script runner."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN_ROOT / 'skills' / 'librarian' / 'scripts'
HOOKS = PLUGIN_ROOT / 'scripts'
PLANNING_ROOT = 'docs/planning'
SUBDIRS = {'adr': 'decision-records', 'fdp': 'feature-designs', 'ap': 'action-plans', 'report': 'reports'}

sys.path.insert(0, str(SCRIPTS))


class Project:
    """A temporary project directory with a planning tree and a config file."""

    def __init__(self, root: Path):
        self.root = root
        self.planning = root / PLANNING_ROOT
        self.planning.mkdir(parents=True)
        self.configure()

    def configure(self, **planning) -> None:
        """Write .claude/vibe-hacker.json; keyword arguments are added to its planning section."""
        config = {
            'planning': {'subdirs': SUBDIRS, **planning},
            'protected_paths': {'planning_root': PLANNING_ROOT},
        }
        path = self.root / '.claude' / 'vibe-hacker.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(config))

    def type_dir(self, doc_type: str) -> Path:
        return self.planning / SUBDIRS[doc_type]

    def write(self, doc_type: str, filename: str, content: str, archived: bool = False) -> Path:
        """Write a document file into a type's directory or its archive."""
        directory = self.type_dir(doc_type) / 'archive' if archived else self.type_dir(doc_type)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        path.write_text(content)
        return path

    def run(self, script: str, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        """Run one of the skill's scripts against this project."""
        env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(self.root)}
        env.pop('CLAUDE_PLUGIN_ROOT', None)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            capture_output=True, text=True, env=env, cwd=self.root, input=stdin,
        )

    def run_hook(self, hook: str) -> subprocess.CompletedProcess:
        """Run one of the plugin's hook scripts against this project."""
        env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(self.root)}
        return subprocess.run(['bash', str(HOOKS / hook)], capture_output=True, text=True, env=env, cwd=self.root)


@pytest.fixture
def project(tmp_path, monkeypatch) -> Project:
    """A project the scripts and the imported modules both resolve to."""
    monkeypatch.setenv('CLAUDE_PROJECT_DIR', str(tmp_path))
    monkeypatch.delenv('CLAUDE_PLUGIN_ROOT', raising=False)
    return Project(tmp_path)


def document(doc_type: str, doc_id: str, status: str, status_body: str | None = None, title: str = 'A title') -> str:
    """Build a document with frontmatter; status_body replaces the bare status under "## Status"."""
    shown = status_body if status_body is not None else status.capitalize()
    return (
        f"---\ntype: {doc_type}\nid: {doc_id}\nstatus: {status}\ncreated: 2026-01-02\nmodified: 2026-01-02\n"
        f"supersedes: null\nsuperseded_by: null\nobsoleted_by: null\nrelated: []\n---\n\n"
        f"# {doc_id}: {title}\n\n## Status\n\n{shown}\n\n## Goal\n\nThe goal.\n\n---\n\n## Addenda\n"
    )
