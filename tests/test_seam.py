"""CLI + HTTP seam tests."""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from grill_me_better.app import create_app
from grill_me_better.paths import round_answers_path
from grill_me_better.session import (
    SessionManifest,
    SessionPhase,
    SessionStatus,
    load_manifest,
    save_manifest,
)
from conftest import seed_active_round


def test_get_active_round_shows_questions_and_recommended(client: TestClient) -> None:
    response = client.get("/round")
    assert response.status_code == 200
    assert "Scope" in response.text
    assert 'value="yes"' in response.text
    assert "checked" in response.text


def test_invalid_round_prompt_shows_validation_detail(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    bad = {**round_one_prompt, "questions": []}
    seed_active_round(grill_workspace, bad)
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/round")
    assert response.status_code == 422
    assert "Invalid round prompt" in response.text
    assert "questions" in response.text.lower()


def test_submit_writes_answers_with_custom_override(
    client: TestClient, grill_workspace: Path
) -> None:
    response = client.post(
        "/round/submit",
        data={
            "q_q1": "yes",
            "custom_q1": "My own scope decision",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    answers_path = round_answers_path(grill_workspace, 1)
    assert answers_path.is_file()
    payload = json.loads(answers_path.read_text(encoding="utf-8"))
    assert payload["answers"][0]["customAnswer"] == "My own scope decision"
    assert payload["answers"][0]["selectedOptionId"] == "yes"
    manifest = load_manifest(grill_workspace)
    assert manifest is not None
    assert manifest.status == SessionStatus.ANSWERS_READY


def test_prior_rounds_render_as_collapsed_history(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt, round_number=1)
    round_answers_path(grill_workspace, 1).write_text(
        json.dumps(
            {
                "round": 1,
                "answers": [
                    {
                        "questionId": "q1",
                        "selectedOptionId": "yes",
                        "customAnswer": None,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    prompt_two = {
        **round_one_prompt,
        "round": 2,
        "title": "Round 2",
        "questions": [
            {
                "id": "q2",
                "title": "Next",
                "bodyMarkdown": "Continue?",
                "options": [{"id": "ok", "label": "OK"}],
                "recommendedOptionId": "ok",
            }
        ],
    }
    (grill_workspace / "round-002.prompt.json").write_text(
        json.dumps(prompt_two, indent=2) + "\n", encoding="utf-8"
    )
    save_manifest(
        grill_workspace,
        SessionManifest(
            port=8765,
            current_round=2,
            status=SessionStatus.WAITING_FOR_ANSWERS,
            phase=SessionPhase.ACTIVE_ROUND,
        ),
    )
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.get("/round")
    assert response.status_code == 200
    assert "<details>" in response.text
    assert "Round 1" in response.text
    assert "Next" in response.text


def test_awaiting_completion_writes_session_complete(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt)
    save_manifest(
        grill_workspace,
        SessionManifest(
            port=8765,
            current_round=1,
            status=SessionStatus.ANSWERS_READY,
            phase=SessionPhase.AWAITING_COMPLETION,
        ),
    )
    client = TestClient(create_app(grill_workspace, planning_repo))
    response = client.post("/round/complete", follow_redirects=False)
    assert response.status_code == 303
    assert (grill_workspace / "session.complete.json").is_file()
    manifest = load_manifest(grill_workspace)
    assert manifest is not None
    assert manifest.phase == SessionPhase.COMPLETE


def test_wait_exits_when_answers_appear(
    grill_workspace: Path, round_one_prompt: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    from grill_me_better.cli import wait_for_round

    seed_active_round(grill_workspace, round_one_prompt)
    answers = round_answers_path(grill_workspace, 1)
    calls = {"n": 0}

    def sleep_and_write(_: float) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            answers.write_text(
                json.dumps({"round": 1, "answers": []}, indent=2) + "\n",
                encoding="utf-8",
            )

    monkeypatch.setattr("grill_me_better.cli.time.sleep", sleep_and_write)
    with pytest.raises(SystemExit) as exc:
        wait_for_round(1)
    assert exc.value.code == 0


def test_resume_keeps_prior_round_files(
    grill_workspace: Path, planning_repo: Path, round_one_prompt: dict
) -> None:
    seed_active_round(grill_workspace, round_one_prompt)
    round_answers_path(grill_workspace, 1).write_text('{"round":1,"answers":[]}\n')
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
    assert client.get("/round").status_code == 200
    assert round_answers_path(grill_workspace, 1).is_file()
    assert (grill_workspace / "round-001.prompt.json").is_file()
