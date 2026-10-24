"""Starlette application for the local grill server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from grill_me_better import html_pages
from grill_me_better.paths import (
    round_answers_path,
    round_prompt_path,
    session_complete_path,
)
from grill_me_better.session import (
    SessionManifest,
    SessionPhase,
    SessionStatus,
    load_manifest,
    save_manifest,
    write_session_complete,
)
from grill_me_better.validation import validate_round_answers, validate_round_prompt


def create_app(workspace: Path) -> Starlette:
    async def get_round(_: Request) -> HTMLResponse:
        manifest = load_manifest(workspace)
        if manifest is None:
            return HTMLResponse(
                html_pages.error_page("No session", ["session.json is missing."]),
                status_code=404,
            )
        if manifest.phase == SessionPhase.COMPLETE:
            return HTMLResponse(
                html_pages.page("Complete", "<h1>Grill session complete</h1>"),
            )
        if manifest.phase == SessionPhase.AWAITING_COMPLETION:
            return HTMLResponse(html_pages.completion_page())
        if manifest.status == SessionStatus.ANSWERS_READY:
            return HTMLResponse(
                html_pages.answers_submitted_page(manifest.current_round)
            )
        return _active_round_response(workspace, manifest)

    async def post_submit(request: Request) -> HTMLResponse:
        manifest = load_manifest(workspace)
        if manifest is None or manifest.phase != SessionPhase.ACTIVE_ROUND:
            return HTMLResponse("Invalid session state", status_code=400)
        prompt = _load_prompt(workspace, manifest.current_round)
        if prompt is None:
            return HTMLResponse(
                html_pages.error_page("Missing prompt", ["Round prompt file not found."]),
                status_code=404,
            )
        form = await request.form()
        answers_payload = _answers_from_form(prompt, form)
        errors = validate_round_answers(answers_payload)
        if errors:
            history = _history_html(workspace, manifest.current_round)
            page = html_pages.active_round_page(
                prompt, history, form_error="; ".join(errors)
            )
            return HTMLResponse(page, status_code=400)
        round_answers_path(workspace, manifest.current_round).write_text(
            json.dumps(answers_payload, indent=2) + "\n", encoding="utf-8"
        )
        updated = SessionManifest(
            host=manifest.host,
            port=manifest.port,
            current_round=manifest.current_round,
            status=SessionStatus.ANSWERS_READY,
            phase=manifest.phase,
        )
        save_manifest(workspace, updated)
        return RedirectResponse("/", status_code=303)

    async def post_complete(_: Request) -> HTMLResponse:
        manifest = load_manifest(workspace)
        if manifest is None:
            return HTMLResponse("No session", status_code=404)
        write_session_complete(workspace)
        done = SessionManifest(
            host=manifest.host,
            port=manifest.port,
            current_round=manifest.current_round,
            status=manifest.status,
            phase=SessionPhase.COMPLETE,
        )
        save_manifest(workspace, done)
        return RedirectResponse("/", status_code=303)

    routes = [
        Route("/", get_round, methods=["GET"]),
        Route("/submit", post_submit, methods=["POST"]),
        Route("/complete", post_complete, methods=["POST"]),
    ]
    return Starlette(routes=routes)


def _active_round_response(workspace: Path, manifest: SessionManifest) -> HTMLResponse:
    prompt = _load_prompt(workspace, manifest.current_round)
    if prompt is None:
        return HTMLResponse(
            html_pages.error_page("Missing prompt", ["Round prompt file not found."]),
            status_code=404,
        )
    errors = validate_round_prompt(prompt)
    if errors:
        return HTMLResponse(
            html_pages.error_page("Invalid round prompt", errors),
            status_code=422,
        )
    history = _history_html(workspace, manifest.current_round)
    return HTMLResponse(html_pages.active_round_page(prompt, history))


def _load_prompt(workspace: Path, round_number: int) -> dict[str, Any] | None:
    path = round_prompt_path(workspace, round_number)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _history_html(workspace: Path, current_round: int) -> str:
    sections: list[str] = []
    for n in range(1, current_round):
        prompt = _load_prompt(workspace, n)
        if prompt is None:
            continue
        ans_path = round_answers_path(workspace, n)
        answers = None
        if ans_path.is_file():
            answers = json.loads(ans_path.read_text(encoding="utf-8"))
        sections.append(html_pages.history_section(n, prompt, answers))
    return "".join(sections)


def _answers_from_form(prompt: dict[str, Any], form: Any) -> dict[str, Any]:
    answers: list[dict[str, Any]] = []
    for q in prompt["questions"]:
        qid = q["id"]
        custom_raw = form.get(f"custom_{qid}")
        custom = str(custom_raw).strip() if custom_raw is not None else ""
        selected_raw = form.get(f"q_{qid}")
        selected = str(selected_raw) if selected_raw is not None else None
        if not custom and not selected and q.get("options"):
            selected = q.get("recommendedOptionId")
        answers.append(
            {
                "questionId": qid,
                "selectedOptionId": selected,
                "customAnswer": custom or None,
            }
        )
    return {"round": int(prompt["round"]), "answers": answers}


def session_is_complete(workspace: Path) -> bool:
    manifest = load_manifest(workspace)
    if manifest and manifest.phase == SessionPhase.COMPLETE:
        return True
    return session_complete_path(workspace).is_file()
