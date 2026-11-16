"""The scripts, run as the skill runs them, against a throwaway project."""

import json
import re
from datetime import date

import frontmatter
from conftest import document

TODAY = date.today().isoformat()
PROSE = "Completed 2026-11-16: merged as #92. What is left is in #91,\n#93 and #94.\n\nDrafted on 2026-11-12."


def fields_of(path) -> dict:
    return frontmatter.parse_frontmatter(path.read_text())[0]


# new.py

def test_new_numbers_from_one_and_fills_the_template(project):
    result = project.run('new.py', 'fdp', 'Gain staging: the output')
    assert result.returncode == 0, result.stderr
    path = project.type_dir('fdp') / 'FDP-001-gain-staging-the-output.md'
    content = path.read_text()
    assert fields_of(path)['id'] == 'FDP-001'
    assert '# FDP-001: Gain staging: the output\n' in content
    assert '${' not in content
    for heading in ('## Status', '## Goal', '## Context', '## Options', '## Questions', '## Steps', '## Done when', '## Addenda'):
        assert f"\n{heading}\n" in content


def test_new_adr_has_no_filename_prefix(project):
    assert project.run('new.py', 'adr', 'Use a thing').returncode == 0
    assert (project.type_dir('adr') / '001-use-a-thing.md').exists()


def test_new_counts_archived_documents(project):
    project.write('fdp', 'FDP-081-live.md', document('fdp', 'FDP-081', 'proposed'))
    project.write('fdp', 'FDP-082-gone.md', document('fdp', 'FDP-082', 'archived'), archived=True)
    project.write('fdp', 'FDP-000-template.md', '# template\n')
    assert project.run('new.py', 'fdp', 'Next one').returncode == 0
    assert (project.type_dir('fdp') / 'FDP-083-next-one.md').exists()


def test_new_refuses_a_retired_type(project):
    project.configure(retired=['ap'])
    result = project.run('new.py', 'ap', 'One more plan')
    assert result.returncode == 1
    assert 'retired' in result.stderr
    assert not project.type_dir('ap').exists()
    assert project.run('new.py', 'fdp', 'Still allowed').returncode == 0


def test_new_refuses_a_title_with_no_slug(project):
    result = project.run('new.py', 'fdp', '???')
    assert result.returncode == 1
    assert not list(project.planning.rglob('*.md'))


def test_new_uses_the_project_template(project):
    override = project.planning / 'templates' / 'fdp.md'
    override.parent.mkdir()
    override.write_text('# FDP-${NUMBER}: ${TITLE}\n\nFrom the project, ${DATE}.\n')
    assert project.run('new.py', 'fdp', 'Mine').returncode == 0
    assert (project.type_dir('fdp') / 'FDP-001-mine.md').read_text() == f"# FDP-001: Mine\n\nFrom the project, {TODAY}.\n"


# update-status.py

def test_update_status_replaces_a_bare_status(project):
    path = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'proposed'))
    result = project.run('update-status.py', 'FDP-001', 'in progress')
    assert result.returncode == 0, result.stderr
    assert fields_of(path)['status'] == 'in progress'
    assert '## Status\n\nIn progress\n\n## Goal' in path.read_text()


def test_update_status_keeps_a_prose_status_whole(project):
    path = project.write('ap', 'AP-053-x.md', document('ap', 'AP-053', 'active', PROSE))
    result = project.run('update-status.py', 'AP-053', 'completed')
    assert result.returncode == 0, result.stderr
    assert f"## Status\n\nCompleted\n\n{PROSE}\n\n## Goal" in path.read_text()
    assert 'archive.py AP-053' in result.stdout


def test_update_status_rejects_a_status_of_another_type(project):
    path = project.write('adr', '001-x.md', document('adr', 'ADR-001', 'proposed'))
    before = path.read_text()
    result = project.run('update-status.py', 'ADR-001', 'completed')
    assert result.returncode == 1
    assert path.read_text() == before


def test_update_status_refuses_an_archived_document(project):
    path = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'archived'), archived=True)
    before = path.read_text()
    result = project.run('update-status.py', 'FDP-001', 'implemented')
    assert result.returncode == 1
    assert 'archived' in result.stderr
    assert path.read_text() == before


# archive.py

def test_archive_moves_the_file_and_leaves_the_note(project):
    project.configure(archive_note='Read with care.')
    live = project.write('ap', 'AP-053-the-well.md', document('ap', 'AP-053', 'completed', PROSE, title='The well'))
    result = project.run('archive.py', 'AP-053')
    assert result.returncode == 0, result.stderr

    archived = project.type_dir('ap') / 'archive' / 'AP-053-the-well.md'
    assert archived.exists() and not live.exists()
    content = archived.read_text()
    assert f"# AP-053: The well\n\n> Archived {TODAY} (was completed). Read with care.\n\n## Status\n" in content
    assert f"## Status\n\nArchived\n\n{PROSE}\n\n## Goal" in content
    assert '## Archived' not in content
    fields = fields_of(archived)
    assert fields['status'] == 'archived' and str(fields['archived']) == TODAY

    index = (project.type_dir('ap') / 'ARCHIVE.md').read_text()
    assert f"| AP-053 | The well | Archived | {TODAY} | [archive/AP-053-the-well.md](archive/AP-053-the-well.md) |" in index


def test_archive_default_note(project):
    project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'implemented'))
    assert project.run('archive.py', 'FDP-001').returncode == 0
    content = (project.type_dir('fdp') / 'archive' / 'FDP-001-x.md').read_text()
    assert f"> Archived {TODAY} (was implemented). A historical record.\n" in content
    assert "## Status\n\nArchived\n\n## Goal" in content


def test_archive_a_document_with_no_status(project):
    project.write('report', 'RPT-019-x.md', '# RPT-019: Notes\n\nText.\n')
    assert project.run('archive.py', 'RPT-019').returncode == 0
    content = (project.type_dir('report') / 'archive' / 'RPT-019-x.md').read_text()
    assert content == f"# RPT-019: Notes\n\n> Archived {TODAY}. A historical record.\n\nText.\n"


def test_archive_index_dates_and_order(project):
    old = document('adr', 'ADR-002', 'archived').replace('modified: 2026-01-02', 'modified: 2026-03-14')
    project.write('adr', '002-older.md', old, archived=True)
    project.write('adr', 'ADR-0001-oldest-name.md', '# ADR-0001 - Oldest\n', archived=True)
    project.write('adr', '003-newer.md', document('adr', 'ADR-003', 'superseded'))
    assert project.run('archive.py', 'ADR-003').returncode == 0
    rows = [line for line in (project.type_dir('adr') / 'ARCHIVE.md').read_text().splitlines() if line.startswith('| ADR')]
    assert [row.split(' | ')[0] for row in rows] == ['| ADR-001', '| ADR-002', '| ADR-003']
    assert ' | 2026-03-14 | ' in rows[1] and f" | {TODAY} | " in rows[2]


def test_archive_refuses_when_the_destination_exists(project):
    live = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'implemented'))
    project.write('fdp', 'FDP-001-x.md', 'already here\n', archived=True)
    before = live.read_text()
    result = project.run('archive.py', 'FDP-001')
    assert result.returncode == 1
    assert live.read_text() == before


def test_archive_refuses_an_archived_document(project):
    project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'archived'), archived=True)
    result = project.run('archive.py', 'FDP-001')
    assert result.returncode == 1
    assert 'already archived' in result.stderr


def test_regenerate_index_removes_an_index_with_no_archive_entries(project):
    (project.type_dir('fdp') / 'archive').mkdir(parents=True)
    index = project.type_dir('fdp') / 'ARCHIVE.md'
    index.write_text('# stale\n')
    assert project.run('archive.py', '--regenerate-index', '--type', 'fdp').returncode == 0
    assert not index.exists()


# append.py, relate.py, supersede.py, edit.py

def test_append_reaches_archived_documents(project):
    path = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'archived'), archived=True)
    assert project.run('append.py', 'fdp-001', 'Later', '--body', 'A note.').returncode == 0
    assert path.read_text().endswith(f"## Addenda\n\n### {TODAY}: Later\n\nA note.\n")


def test_relate_both_ways(project):
    fdp = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'proposed'))
    adr = project.write('adr', '002-y.md', document('adr', 'ADR-002', 'accepted'))
    assert project.run('relate.py', 'FDP-001', 'adr-002', '--bidirectional').returncode == 0
    assert fields_of(fdp)['related'] == ['ADR-002']
    assert fields_of(adr)['related'] == ['FDP-001']
    assert project.run('relate.py', 'FDP-001', 'RPT-009').returncode == 1


def test_supersede_links_both_documents(project):
    old = project.write('adr', '001-x.md', document('adr', 'ADR-001', 'accepted', PROSE))
    result = project.run('supersede.py', 'ADR-001', 'A better way')
    assert result.returncode == 0, result.stderr
    new = project.type_dir('adr') / '002-a-better-way.md'
    assert fields_of(new)['supersedes'] == 'ADR-001'
    assert fields_of(old)['superseded_by'] == 'ADR-002' and fields_of(old)['status'] == 'superseded'
    content = old.read_text()
    assert f"## Status\n\nSuperseded\n\n{PROSE}\n" in content
    assert content.endswith(f"### {TODAY}: Superseded\n\nThis document has been superseded by ADR-002.\n")


def test_supersede_refuses_a_retired_type(project):
    project.configure(retired=['ap'])
    old = project.write('ap', 'AP-001-x.md', document('ap', 'AP-001', 'active'))
    before = old.read_text()
    result = project.run('supersede.py', 'AP-001', 'Again')
    assert result.returncode == 1
    assert old.read_text() == before
    assert len(list(project.type_dir('ap').glob('*.md'))) == 1


def test_edit_exit_codes(project):
    open_doc = project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'in progress'))
    project.write('fdp', 'FDP-002-y.md', document('fdp', 'FDP-002', 'implemented'))
    project.write('fdp', 'FDP-003-z.md', document('fdp', 'FDP-003', 'archived'), archived=True)

    result = project.run('edit.py', 'FDP-001')
    assert result.returncode == 0 and result.stdout.strip() == str(open_doc)
    locked = project.run('edit.py', 'FDP-002')
    assert locked.returncode == 1 and 'read-only' in locked.stderr
    assert project.run('edit.py', 'FDP-002', '--force').returncode == 0
    assert project.run('edit.py', 'FDP-003').returncode == 1
    assert project.run('edit.py', 'FDP-004').returncode == 2
    assert project.run('edit.py', 'nonsense').returncode == 2


# list.py, review.py

def test_list_marks_archived_documents(project):
    project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'proposed', title='Live one'))
    project.write('fdp', 'FDP-002-y.md', document('fdp', 'FDP-002', 'archived', title='Old one'), archived=True)
    live_only = project.run('list.py').stdout
    assert 'Live one' in live_only and 'Old one' not in live_only
    everything = project.run('list.py', '--include-archived').stdout
    assert re.search(r'FDP-002 .*\[A\] Archived .*Old one', everything)


def test_review_separates_open_from_finished(project):
    project.configure(retired=['ap'])
    project.write('fdp', 'FDP-001-x.md', document('fdp', 'FDP-001', 'in progress', title='Open design'))
    project.write('fdp', 'FDP-002-y.md', document('fdp', 'FDP-002', 'implemented', title='Built design'))
    project.write('ap', 'AP-001-x.md', document('ap', 'AP-001', 'active', PROSE, title='Open plan'))
    project.write('ap', 'AP-002-y.md', document('ap', 'AP-002', 'abandoned', title='Dropped plan'))
    project.write('adr', '001-x.md', document('adr', 'ADR-001', 'accepted', title='Standing decision'))
    project.write('fdp', 'FDP-003-z.md', document('fdp', 'FDP-003', 'archived', title='Gone'), archived=True)

    output = project.run('review.py').stdout
    open_part, finished_part = output.split('Finished, not archived: 2 total')
    assert 'Open planning documents: 2 total' in open_part
    assert 'Open design' in open_part and 'Open plan' in open_part
    assert '## AP (retired type) (1)' in open_part
    assert 'The goal.' in open_part and 'Drafted on' not in open_part
    assert 'Built design' in finished_part and 'Dropped plan' in finished_part
    assert 'Standing decision' not in output and 'Gone' not in output


def test_review_all_clear(project):
    project.write('adr', '001-x.md', document('adr', 'ADR-001', 'accepted'))
    assert project.run('review.py').stdout.startswith('All clear')


# log.py

def test_log_creates_then_appends(project):
    result = project.run('log.py', 'davis', 'First listening', '--body', '> "Sounds good"\n\nSource: chat.')
    assert result.returncode == 0, result.stderr
    path = project.planning / 'logs' / 'davis.md'
    assert path.read_text() == f"# davis: log\n\n### {TODAY}: First listening\n\n> \"Sounds good\"\n\nSource: chat.\n"

    assert project.run('log.py', 'davis', 'Second', '--body', '-', stdin='From stdin.\n').returncode == 0
    assert path.read_text().endswith(f"Source: chat.\n\n### {TODAY}: Second\n\nFrom stdin.\n")


def test_log_keeps_an_existing_header(project):
    path = project.planning / 'logs' / 'davis.md'
    path.parent.mkdir()
    path.write_text("# Davis: decisions and listening log\n\nWhat it is.\n")
    assert project.run('log.py', 'davis', 'Entry', '--body', 'Text.').returncode == 0
    assert path.read_text() == f"# Davis: decisions and listening log\n\nWhat it is.\n\n### {TODAY}: Entry\n\nText.\n"


def test_log_rejects_a_path_as_thread_name(project):
    for thread in ('../escape', 'Davis', 'a/b', ''):
        assert project.run('log.py', thread, 'Entry').returncode == 1
    assert not (project.planning / 'logs').exists()


# init-roadmap.py and the PreCompact hook

def test_roadmap_template_and_reminder(project):
    assert project.run('init-roadmap.py').returncode == 0
    roadmap = (project.planning / 'roadmap.md').read_text()
    assert f"> Last updated: {TODAY}\n" in roadmap
    assert '## Now\n' in roadmap and '## Next\n' in roadmap and 'Recently Completed' not in roadmap
    assert project.run('init-roadmap.py').returncode == 1

    message = json.loads(project.run_hook('precompact-roadmap.sh').stdout)['systemMessage']
    assert 'docs/planning/roadmap.md' in message and "'Now'" in message and 'Recently Completed' not in message


def test_reminder_is_silent_for_a_stale_roadmap(project):
    (project.planning / 'roadmap.md').write_text('# Roadmap\n\n> Last updated: 2020-01-01\n')
    result = project.run_hook('precompact-roadmap.sh')
    assert result.returncode == 0 and result.stdout == ''
