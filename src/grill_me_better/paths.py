"""Grill workspace path conventions."""

from __future__ import annotations

import os
from pathlib import Path

SESSION_MANIFEST_NAME = "session.json"
SESSION_COMPLETE_NAME = "session.complete.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT_START = 8765


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def schema_path(name: str) -> Path:
    return package_root() / "schemas" / name


def resolve_grill_workspace(cwd: Path | None = None) -> Path:
    override = os.environ.get("GRILL_WORKSPACE_ROOT")
    if override:
        return Path(override)
    base = cwd or Path.cwd()
    return base / ".grill"


def round_prompt_path(workspace: Path, round_number: int) -> Path:
    return workspace / f"round-{round_number:03d}.prompt.json"


def round_answers_path(workspace: Path, round_number: int) -> Path:
    return workspace / f"round-{round_number:03d}.answers.json"


def session_manifest_path(workspace: Path) -> Path:
    return workspace / SESSION_MANIFEST_NAME


def session_complete_path(workspace: Path) -> Path:
    return workspace / SESSION_COMPLETE_NAME
