"""Phase A hub seam tests (UI hub v2 ticket 06)."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from grill_me_better.app import create_app
from conftest import seed_active_round


def test_dashboard_links_to_artifacts(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/artifacts/glossary"' in response.text


def test_glossary_tab_lists_file(planning_repo: Path, grill_workspace: Path) -> None:
    (planning_repo / "GLOSSARY.md").write_text("# G\n\n## Language\n\n**Term**:\nDef\n")
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/artifacts/glossary")
    assert response.status_code == 200
    assert "GLOSSARY.md" in response.text


def test_artifact_view_renders_mermaid(planning_repo: Path, grill_workspace: Path) -> None:
    (planning_repo / "diagram.md").write_text(
        "# D\n\n```mermaid\ngraph LR\n  A-->B\n```\n"
    )
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/artifact?path=diagram.md")
    assert response.status_code == 200
    assert 'class="mermaid"' in response.text
    assert "/static/mermaid.min.js" in response.text


def test_split_round_includes_context_panel(client: TestClient, planning_repo: Path) -> None:
    (planning_repo / "GLOSSARY.md").write_text("# G\n\n**Foo**:\nBar\n")
    response = client.get("/round")
    assert response.status_code == 200
    assert "aside" in response.text
    assert "Context" in response.text


def test_glossary_empty_state(planning_repo: Path, grill_workspace: Path) -> None:
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/artifacts/glossary")
    assert "No files found" in response.text


def test_glossary_edit_preview_and_save(planning_repo: Path, grill_workspace: Path) -> None:
    (planning_repo / "GLOSSARY.md").write_text(
        "# G\n\n## Language\n\n**Old**:\nOld def\n"
    )
    client = TestClient(create_app(grill_workspace, planning_repo))
    preview = client.post(
        "/edit/glossary/preview",
        data={
            "title": "G",
            "preamble": "",
            "term_count": "1",
            "name_0": "Old",
            "definition_0": "New def",
            "avoid_0": "alias",
            "new_name": "NewTerm",
            "new_definition": "Extra term",
            "new_avoid": "",
        },
    )
    assert preview.status_code == 200
    assert "Preview changes" in preview.text
    confirm = client.post(
        "/edit/confirm",
        data={
            "path": "GLOSSARY.md",
            "content": "# G\n\n## Language\n\n**Old**:\nNew def\n_Avoid_: alias\n\n**NewTerm**:\nExtra term\n",
        },
        follow_redirects=False,
    )
    assert confirm.status_code == 303
    assert "NewTerm" in (planning_repo / "GLOSSARY.md").read_text()
