"""The type table's lookups: IDs, files, templates and the planning config keys."""

import pytest

import config
from conftest import document


@pytest.mark.parametrize('doc_id, expected', [
    ('ADR-001', ('adr', 1)),
    ('fdp-081', ('fdp', 81)),
    ('AP-53', ('ap', 53)),
    ('RPT-0007', ('report', 7)),
    (' FDP-002 ', ('fdp', 2)),
])
def test_parse_doc_id(doc_id, expected):
    assert config.parse_doc_id(doc_id) == expected


@pytest.mark.parametrize('doc_id', ['FDP', 'FDP-', 'XYZ-001', '001', 'FDP-1a', 'FDP_001', ''])
def test_parse_doc_id_rejects(doc_id):
    with pytest.raises(ValueError):
        config.parse_doc_id(doc_id)


def test_id_examples_names_every_type():
    examples = config.id_examples()
    assert all(config.get_id_prefix(doc_type) + '-001' in examples for doc_type in config.DEFAULT_TYPES)


def test_find_document_per_type(project):
    documents = {
        ('adr', 3): project.write('adr', '003-a-decision.md', document('adr', 'ADR-003', 'accepted')),
        ('fdp', 81): project.write('fdp', 'FDP-081-a-design.md', document('fdp', 'FDP-081', 'proposed')),
        ('ap', 53): project.write('ap', 'AP-053-a-plan.md', document('ap', 'AP-053', 'active')),
        ('report', 12): project.write('report', 'RPT-012-a-report.md', document('report', 'RPT-012', 'draft')),
    }
    for (doc_type, number), path in documents.items():
        assert config.find_document(doc_type, number, project.root) == path


def test_find_document_matches_the_number_not_its_padding(project):
    path = project.write('fdp', 'FDP-0007-wide.md', document('fdp', 'FDP-007', 'proposed'))
    assert config.find_document_by_id('FDP-7', project.root) == path


def test_find_document_ignores_other_files(project):
    project.write('fdp', 'ARCHIVE.md', '# Archived\n')
    project.write('fdp', 'FDP-000-template.md', '# FDP-000\n')
    project.write('adr', 'README.md', '# Decisions\n')
    assert config.find_document('fdp', 1, project.root) is None
    assert config.find_document('adr', 1, project.root) is None


def test_find_document_in_archive(project):
    path = project.write('fdp', 'FDP-020-old.md', document('fdp', 'FDP-020', 'archived'), archived=True)
    assert config.find_document('fdp', 20, project.root) == path
    assert config.find_document('fdp', 20, project.root, search_archive=False) is None
    assert config.is_archived(path)


def test_find_document_prefers_the_live_file(project):
    project.write('ap', 'AP-001-old.md', document('ap', 'AP-001', 'archived'), archived=True)
    live = project.write('ap', 'AP-001-new.md', document('ap', 'AP-001', 'active'))
    assert config.find_document('ap', 1, project.root) == live
    assert not config.is_archived(live)


def test_find_document_by_id_missing(project):
    with pytest.raises(FileNotFoundError):
        config.find_document_by_id('FDP-404', project.root)


def test_is_archived_looks_at_the_parent_directory_only(tmp_path):
    assert not config.is_archived(tmp_path / 'archive' / 'docs' / 'planning' / 'feature-designs' / 'FDP-001-x.md')


def test_retired_and_archive_note_defaults(project):
    assert config.get_retired_types() == []
    assert not config.is_retired('ap')
    assert config.get_archive_note() == config.DEFAULT_ARCHIVE_NOTE


def test_retired_and_archive_note_from_config(project):
    project.configure(retired=['AP'], archive_note='Read with care.')
    assert config.is_retired('ap')
    assert not config.is_retired('fdp')
    assert config.get_archive_note() == 'Read with care.'


def test_subdirs_come_from_config(project):
    assert config.get_doc_dir('adr') == 'docs/planning/decision-records'
    assert config.get_logs_dir() == 'docs/planning/logs'


def test_builtin_template_for_every_type(project):
    for doc_type in config.DEFAULT_TYPES:
        path = config.get_template_path(doc_type, project.root)
        assert path is not None and path.parent == config.BUILTIN_TEMPLATES


def test_project_template_overrides_the_builtin(project):
    override = project.planning / 'templates' / 'fdp.md'
    override.parent.mkdir()
    override.write_text('# FDP-${NUMBER}: ${TITLE}\n')
    assert config.get_template_path('fdp', project.root) == override
    assert config.get_template_path('adr', project.root).parent == config.BUILTIN_TEMPLATES
