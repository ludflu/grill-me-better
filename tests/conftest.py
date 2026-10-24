"""Shared test fixtures."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from grill_me_better.app import create_app
from grill_me_better.paths import package_root
from grill_me_better.session import (
    SessionManifest,
    SessionPhase,
    SessionStatus,
    save_manifest,
)


@pytest.fixture()
def grill_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    workspace = tmp_path / "grill"
    workspace.mkdir()
    monkeypatch.setenv("GRILL_WORKSPACE_ROOT", str(workspace))
    return workspace


@pytest.fixture()
def planning_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    planning = tmp_path / "planning"
    planning.mkdir()
    monkeypatch.setenv("GRILL_PLANNING_ROOT", str(planning))
    return planning


@pytest.fixture()
def round_one_prompt() -> dict:
    path = package_root() / "fixtures" / "round-001.prompt.json"
    return json.loads(path.read_text(encoding="utf-8"))


def seed_active_round(
    workspace: Path,
    prompt: dict,
    *,
    port: int = 8765,
    round_number: int | None = None,
) -> SessionManifest:
    workspace.mkdir(parents=True, exist_ok=True)
    rnd = round_number if round_number is not None else int(prompt["round"])
    prompt = {**prompt, "round": rnd}
    (workspace / f"round-{rnd:03d}.prompt.json").write_text(
        json.dumps(prompt, indent=2) + "\n", encoding="utf-8"
    )
    manifest = SessionManifest(
        port=port,
        current_round=rnd,
        status=SessionStatus.WAITING_FOR_ANSWERS,
        phase=SessionPhase.ACTIVE_ROUND,
    )
    save_manifest(workspace, manifest)
    return manifest


@pytest.fixture()
def client(
    grill_workspace: Path,
    planning_repo: Path,
    round_one_prompt: dict,
) -> TestClient:
    seed_active_round(grill_workspace, round_one_prompt)
    return TestClient(create_app(grill_workspace, planning_repo))
