"""Glossary view and full-file editor."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from grill_me_better.app import create_app
from grill_me_better.glossary import parse_glossary, render_glossary


SAMPLE = """# Grill Me Better

Intro paragraph.

## Language

**Grill session**:
A single planning interview.
_Avoid_: Chat

**Round**:
One batch of questions.
_Avoid_: Wave
"""


def test_glossary_view_lists_all_terms(planning_repo: Path, grill_workspace: Path) -> None:
    (planning_repo / "GLOSSARY.md").write_text(SAMPLE)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/glossary")
    assert response.status_code == 200
    assert "Grill session" in response.text
    assert "Round" in response.text
    assert "Edit glossary" in response.text


def test_glossary_edit_form_lists_each_term(planning_repo: Path, grill_workspace: Path) -> None:
    (planning_repo / "GLOSSARY.md").write_text(SAMPLE)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/edit/glossary")
    assert response.status_code == 200
    assert 'name="name_0"' in response.text
    assert 'name="name_1"' in response.text


def test_glossary_save_round_trip(planning_repo: Path, grill_workspace: Path) -> None:
    path = planning_repo / "GLOSSARY.md"
    path.write_text(SAMPLE)
    client = TestClient(create_app(grill_workspace, planning_repo))
    doc = parse_glossary(SAMPLE)
    doc.terms[0].definition = "Updated definition."
    after = render_glossary(doc)
    preview = client.post(
        "/edit/glossary/preview",
        data={
            "title": doc.title,
            "preamble": doc.preamble,
            "term_count": str(len(doc.terms)),
            "name_0": doc.terms[0].name,
            "definition_0": "Updated definition.",
            "avoid_0": doc.terms[0].avoid,
            "name_1": doc.terms[1].name,
            "definition_1": doc.terms[1].definition,
            "avoid_1": doc.terms[1].avoid,
            "new_name": "",
            "new_definition": "",
            "new_avoid": "",
        },
    )
    assert preview.status_code == 200
    confirm = client.post(
        "/edit/confirm",
        data={"path": "GLOSSARY.md", "content": after},
        follow_redirects=False,
    )
    assert confirm.status_code == 303
    assert confirm.headers["location"] == "/glossary"
    assert "Updated definition." in path.read_text()
