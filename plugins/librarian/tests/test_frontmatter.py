"""Document text operations: the Status section, frontmatter, addenda and the archive note."""

from datetime import date

import pytest

import frontmatter
from conftest import document

TODAY = date.today().isoformat()
PROSE = "Completed 2026-11-16: merged as #92. What is left is in #91,\n#93 and #94.\n\nDrafted on 2026-11-12."


def test_bare_status_is_replaced():
    content, found = frontmatter.set_body_status("# T\n\n## Status\n\nProposed\n\n## Goal\n", 'accepted')
    assert found
    assert content == "# T\n\n## Status\n\nAccepted\n\n## Goal\n"


def test_multi_word_status_keeps_one_capital():
    content, _ = frontmatter.set_body_status("## Status\n\nProposed\n", 'in progress')
    assert content == "## Status\n\nIn progress\n"
    content, _ = frontmatter.set_body_status(content, 'implemented')
    assert content == "## Status\n\nImplemented\n"


def test_prose_status_is_kept_whole():
    before = f"# T\n\n## Status\n\n{PROSE}\n\n## Goal\n\nG\n"
    content, found = frontmatter.set_body_status(before, 'archived')
    assert found
    assert content == f"# T\n\n## Status\n\nArchived\n\n{PROSE}\n\n## Goal\n\nG\n"


def test_status_above_prose_is_replaced_next_time():
    content, _ = frontmatter.set_body_status(f"## Status\n\n{PROSE}\n", 'completed')
    content, _ = frontmatter.set_body_status(content, 'archived')
    assert content == f"## Status\n\nArchived\n\n{PROSE}\n"


def test_only_the_first_top_level_status_heading_changes():
    before = "# T\n\n## Status\n\nActive\n\n## Phases\n\n### Status\n\nPhase 1 done\n\n## Status\n\nLeft alone\n"
    content, _ = frontmatter.set_body_status(before, 'completed')
    assert content == before.replace("## Status\n\nActive", "## Status\n\nCompleted", 1)
    assert "### Status\n\nPhase 1 done" in content and "## Status\n\nLeft alone" in content


def test_deeper_status_heading_alone_is_not_a_status_section():
    before = "# T\n\n### Status of the build\n\nFine\n"
    assert frontmatter.set_body_status(before, 'completed') == (before, False)


def test_status_without_a_blank_line_and_empty_section():
    content, _ = frontmatter.set_body_status("## Status\nProposed\n## Goal\n", 'accepted')
    assert content == "## Status\nAccepted\n## Goal\n"
    content, _ = frontmatter.set_body_status("## Status\n\n## Goal\n", 'accepted')
    assert content == "## Status\n\nAccepted\n\n## Goal\n"


def test_set_status_updates_frontmatter_and_body():
    content = frontmatter.set_status(document('ap', 'AP-001', 'active', PROSE), 'Completed', {'note': 'x'})
    fields, body = frontmatter.parse_frontmatter(content)
    assert fields['status'] == 'completed'
    assert fields['note'] == 'x'
    assert str(fields['modified']) == TODAY
    assert f"## Status\n\nCompleted\n\n{PROSE}\n" in body
    assert frontmatter.document_status(content) == 'completed'


@pytest.mark.skipif(not frontmatter.HAS_YAML, reason='the fallback writer never quotes')
def test_modified_date_is_written_unquoted():
    content = frontmatter.set_status(document('ap', 'AP-001', 'active'), 'completed')
    assert f"\nmodified: {TODAY}\n" in content
    assert "created: 2026-01-02\n" in content


def test_set_status_without_frontmatter():
    content = frontmatter.set_status("# Old\n\n## Status\n\nDraft\n", 'published')
    assert content == "# Old\n\n## Status\n\nPublished\n"
    assert frontmatter.document_status(content) == 'Published'


def test_set_status_with_nothing_to_set():
    with pytest.raises(ValueError):
        frontmatter.set_status("# Old\n\nNo status here.\n", 'published')


def test_note_goes_under_the_title():
    content = frontmatter.insert_note_under_title(document('fdp', 'FDP-001', 'implemented'), 'Archived. Old.')
    assert "# FDP-001: A title\n\n> Archived. Old.\n\n## Status\n" in content
    assert content.startswith('---\ntype: fdp\n')


def test_note_without_a_title_goes_first():
    assert frontmatter.insert_note_under_title("## Status\n\nDraft\n", 'N.') == "> N.\n\n## Status\n\nDraft\n"
    with_fields = frontmatter.insert_note_under_title("---\nid: X-1\n---\n\nText\n", 'N.')
    assert with_fields == "---\nid: X-1\n---\n> N.\n\nText\n"


def test_append_addendum_to_existing_section():
    content = frontmatter.append_addendum(document('adr', 'ADR-001', 'accepted'), 'A note', 'Body text.\n\n')
    assert content.endswith(f"## Addenda\n\n### {TODAY}: A note\n\nBody text.\n")
    second = frontmatter.append_addendum(content, 'Another', 'More.')
    assert second.endswith(f"Body text.\n\n### {TODAY}: Another\n\nMore.\n")
    assert second.count('## Addenda') == 1


def test_append_addendum_creates_the_section():
    content = frontmatter.append_addendum("# Old\n\nText.\n", 'A note', 'Body.')
    assert content == f"# Old\n\nText.\n\n---\n\n## Addenda\n\n### {TODAY}: A note\n\nBody.\n"


@pytest.mark.parametrize('heading, title', [
    ('# ADR-001: Use a thing', 'Use a thing'),
    ('# FDP-081: Membrane pair', 'Membrane pair'),
    ('# RPT-7: A report', 'A report'),
    ('# No identifier', 'No identifier'),
])
def test_extract_title(heading, title):
    assert frontmatter.extract_title_from_body(f"{heading}\n\n## Status\n") == title
