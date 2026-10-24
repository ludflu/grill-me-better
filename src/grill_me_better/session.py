"""Session manifest read/write."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from grill_me_better.paths import session_complete_path, session_manifest_path


class SessionPhase(StrEnum):
    ACTIVE_ROUND = "active_round"
    AWAITING_COMPLETION = "awaiting_completion"
    COMPLETE = "complete"


class SessionStatus(StrEnum):
    WAITING_FOR_ANSWERS = "waiting_for_answers"
    ANSWERS_READY = "answers_ready"


@dataclass(frozen=True)
class SessionManifest:
    port: int
    current_round: int
    status: SessionStatus
    phase: SessionPhase = SessionPhase.ACTIVE_ROUND
    host: str = "127.0.0.1"

    def to_json(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "currentRound": self.current_round,
            "status": self.status.value,
            "phase": self.phase.value,
        }

    @staticmethod
    def from_json(data: dict[str, Any]) -> SessionManifest:
        phase_raw = data.get("phase", SessionPhase.ACTIVE_ROUND.value)
        return SessionManifest(
            host=str(data.get("host", "127.0.0.1")),
            port=int(data["port"]),
            current_round=int(data["currentRound"]),
            status=SessionStatus(data["status"]),
            phase=SessionPhase(phase_raw),
        )


def load_manifest(workspace: Path) -> SessionManifest | None:
    path = session_manifest_path(workspace)
    if not path.is_file():
        return None
    return SessionManifest.from_json(json.loads(path.read_text(encoding="utf-8")))


def save_manifest(workspace: Path, manifest: SessionManifest) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    path = session_manifest_path(workspace)
    path.write_text(json.dumps(manifest.to_json(), indent=2) + "\n", encoding="utf-8")


def write_session_complete(workspace: Path, confirmed: bool = True) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    payload = {"confirmed": confirmed}
    session_complete_path(workspace).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
