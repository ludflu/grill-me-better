"""Seam tests for structured artifact editors (tickets 08-09)."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from grill_me_better.app import create_app


def test_adr_edit_preview_and_save(planning_repo: Path, grill_workspace: Path) -> None:
    adr_dir = planning_repo / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    path = adr_dir / "0001-test.md"
    path.write_text("# Old title\n\nOld body.\n")
    client = TestClient(create_app(grill_workspace, planning_repo))
    rel = "docs/adr/0001-test.md"
    preview = client.post(
        "/edit/adr/preview",
        data={"path": rel, "title": "New title", "body": "New body text."},
    )
    assert preview.status_code == 200
    assert "Preview changes" in preview.text
    confirm = client.post(
        "/edit/confirm",
        data={"path": rel, "content": "# New title\n\nNew body text.\n"},
        follow_redirects=False,
    )
    assert confirm.status_code == 303
    assert "New title" in path.read_text()


def test_adr_preview_rejects_empty_title(planning_repo: Path, grill_workspace: Path) -> None:
    adr_dir = planning_repo / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    path = adr_dir / "0001-test.md"
    path.write_text("# Title\n\nBody\n")
    client = TestClient(create_app(grill_workspace, planning_repo))
    preview = client.post(
        "/edit/adr/preview",
        data={"path": "docs/adr/0001-test.md", "title": "", "body": "Body"},
    )
    assert preview.status_code == 400


def test_spec_edit_save(planning_repo: Path, grill_workspace: Path) -> None:
    spec = planning_repo / "docs" / "SPEC-test.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        "# Spec\n\n## Problem Statement\n\nOld problem\n\n## Solution\n\nOld sol\n"
    )
    rel = "docs/SPEC-test.md"
    client = TestClient(create_app(grill_workspace, planning_repo))
    preview = client.post(
        "/edit/spec/preview",
        data={
            "path": rel,
            "title": "Spec",
            "problem": "New problem",
            "solution": "New solution",
        },
    )
    assert preview.status_code == 200
    client.post(
        "/edit/confirm",
        data={
            "path": rel,
            "content": "# Spec\n\n## Problem Statement\n\nNew problem\n\n## Solution\n\nNew solution\n\n",
        },
    )
    text = spec.read_text()
    assert "New problem" in text
    assert "New solution" in text


def test_ticket_edit_save(planning_repo: Path, grill_workspace: Path) -> None:
    issues = planning_repo / ".scratch" / "demo" / "issues"
    issues.mkdir(parents=True)
    ticket = issues / "01-demo.md"
    ticket.write_text("# Old\n\n**What to build:** x\n\n**Blocked by:** None\n\n- [ ] a\n")
    rel = ".scratch/demo/issues/01-demo.md"
    client = TestClient(create_app(grill_workspace, planning_repo))
    preview = client.post(
        "/edit/ticket/preview",
        data={
            "path": rel,
            "title": "Demo ticket",
            "what_to_build": "Build the thing",
            "acceptance": "- [ ] Done",
            "blocked_by": "None",
        },
    )
    assert preview.status_code == 200
    client.post(
        "/edit/confirm",
        data={
            "path": rel,
            "content": (
                "# Demo ticket\n\n**What to build:** Build the thing\n\n"
                "**Blocked by:** None\n\n**Status:** ready-for-agent\n\n- [ ] Done\n"
            ),
        },
    )
    assert "Build the thing" in ticket.read_text()
