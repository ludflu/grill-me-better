"""CLI entry point for grill-me-better."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import uvicorn

from grill_me_better.app import create_app
from grill_me_better.paths import (
    DEFAULT_HOST,
    resolve_grill_workspace,
    resolve_planning_repo_root,
    round_prompt_path,
)
from grill_me_better.port import pick_port, resolve_serve_port
from grill_me_better.session import (
    SessionManifest,
    SessionPhase,
    SessionStatus,
    load_manifest,
    save_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="grill-me-better")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("serve", help="Start or resume the local grill server")

    wait_p = sub.add_parser("wait", help="Block until round answers exist")
    wait_p.add_argument("--round", type=int, required=True, dest="round_number")

    args = parser.parse_args()
    if args.command == "serve":
        serve()
    elif args.command == "wait":
        wait_for_round(args.round_number)


def serve() -> None:
    workspace = resolve_grill_workspace()
    workspace.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(workspace)
    if manifest is None:
        port = pick_port(DEFAULT_HOST)
        manifest = _manifest_from_prompt(workspace, port)
        if manifest is None:
            print(
                "No session.json and no round prompt found. "
                "Write round-NNN.prompt.json first.",
                file=sys.stderr,
            )
            sys.exit(1)
        save_manifest(workspace, manifest)
    elif manifest.phase != SessionPhase.COMPLETE:
        host = manifest.host or DEFAULT_HOST
        old_port = manifest.port
        port = resolve_serve_port(host, manifest.port or None)
        if port != old_port:
            if old_port:
                print(
                    f"Port {old_port} is in use; serving on {port} instead.",
                    file=sys.stderr,
                )
            manifest = SessionManifest(
                host=host,
                port=port,
                current_round=manifest.current_round,
                status=manifest.status,
                phase=manifest.phase,
            )
            save_manifest(workspace, manifest)
    else:
        host = manifest.host or DEFAULT_HOST
        port = resolve_serve_port(host, manifest.port or None)

    planning_root = resolve_planning_repo_root()
    app = create_app(workspace, planning_root)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _manifest_from_prompt(workspace: Path, port: int) -> SessionManifest | None:
    for path in sorted(workspace.glob("round-*.prompt.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionManifest(
            port=port,
            current_round=int(data["round"]),
            status=SessionStatus.WAITING_FOR_ANSWERS,
            phase=SessionPhase.ACTIVE_ROUND,
        )
    return None


def wait_for_round(round_number: int, poll_seconds: float = 0.25) -> None:
    workspace = resolve_grill_workspace()
    answers = workspace / f"round-{round_number:03d}.answers.json"
    while not answers.is_file():
        time.sleep(poll_seconds)
    answers.read_text(encoding="utf-8")
    sys.exit(0)


if __name__ == "__main__":
    main()
