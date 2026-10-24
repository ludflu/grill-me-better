"""Hub routing and planning repo root (UI hub v2 ticket 01)."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from grill_me_better.app import create_app
from grill_me_better.paths import resolve_planning_repo_root
from grill_me_better.session import (
    SessionManifest,
    SessionPhase,
    SessionStatus,
    save_manifest,
)
from conftest import seed_active_round


def test_planning_repo_root_separate_from_grill_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    grill = tmp_path / "grill"
    planning = tmp_path / "planning"
    grill.mkdir()
    planning.mkdir()
    monkeypatch.setenv("GRILL_WORKSPACE_ROOT", str(grill))
    monkeypatch.setenv("GRILL_PLANNING_ROOT", str(planning))
    assert resolve_planning_repo_root() == planning


def test_dashboard_at_root_includes_hub_navigation(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/")
    assert response.status_code == 200
    assert "Session dashboard" in response.text
    assert 'href="/round"' in response.text


def test_active_round_lives_at_round_route(client: TestClient) -> None:
    response = client.get("/round")
    assert response.status_code == 200
    assert "Scope" in response.text
    assert 'action="/round/submit"' in response.text


def test_root_does_not_show_active_round_form(client: TestClient) -> None:
    response = client.get("/")
    assert "Submit round" not in response.text


def test_submit_via_round_route(
    client: TestClient, grill_workspace: Path
) -> None:
    response = client.post(
        "/round/submit",
        data={"q_q1": "yes", "custom_q1": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/round"


def test_invalid_prompt_on_round_route(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    bad = {**round_one_prompt, "questions": []}
    seed_active_round(grill_workspace, bad)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/round")
    assert response.status_code == 422
    assert "Invalid round prompt" in response.text


def test_answers_ready_on_round_route(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt)
    save_manifest(
        grill_workspace,
        SessionManifest(
            port=8765,
            current_round=1,
            status=SessionStatus.ANSWERS_READY,
            phase=SessionPhase.ACTIVE_ROUND,
        ),
    )
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/round")
    assert response.status_code == 200
    assert "submitted" in response.text.lower()
