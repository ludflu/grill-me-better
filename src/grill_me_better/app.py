"""Starlette application for the local grill server."""

from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from grill_me_better import html_pages
from grill_me_better.artifacts import (
    EMPTY_HELP,
    KIND_LABELS,
    discover_by_kind,
    resolve_safe_path,
)
from grill_me_better.diff_preview import unified_diff
from grill_me_better.editors import (
    parse_adr_form,
    parse_glossary_form,
    parse_spec_form,
    parse_ticket_form,
    render_adr,
    render_glossary,
    render_spec,
    render_ticket,
)
from grill_me_better.markdown_view import markdown_to_view_html
from grill_me_better.paths import (
    ROUND_COMPLETE_ROUTE,
    ROUND_ROUTE,
    ROUND_SUBMIT_ROUTE,
    resolve_planning_repo_root,
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

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    workspace: Path,
    planning_root: Path | None = None,
) -> Starlette:
    planning = planning_root or resolve_planning_repo_root()

    async def get_dashboard(_: Request) -> HTMLResponse:
        manifest = load_manifest(workspace)
        if manifest is None:
            page = html_pages.dashboard_page(
                has_session=False,
                phase=None,
                status=None,
                current_round=None,
            )
            return HTMLResponse(page)
        page = html_pages.dashboard_page(
            has_session=True,
            phase=manifest.phase.value,
            status=manifest.status.value,
            current_round=manifest.current_round,
        )
        return HTMLResponse(page)

    async def get_round(_: Request) -> HTMLResponse:
        manifest = load_manifest(workspace)
        if manifest is None:
            return HTMLResponse(
                html_pages.error_page("No session", ["session.json is missing."]),
                status_code=404,
            )
        if manifest.phase == SessionPhase.COMPLETE:
            body = "<h1>Grill session complete</h1><p><a href=\"/\">Dashboard</a></p>"
            return HTMLResponse(html_pages.hub_shell("Complete", body, active="round"))
        if manifest.phase == SessionPhase.AWAITING_COMPLETION:
            return HTMLResponse(html_pages.completion_page())
        if manifest.status == SessionStatus.ANSWERS_READY:
            return HTMLResponse(
                html_pages.answers_submitted_page(manifest.current_round)
            )
        return _active_round_response(workspace, planning, manifest)

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
            ctx = _context_panel(planning)
            page = html_pages.active_round_page(
                prompt, history, form_error="; ".join(errors), context_panel=ctx
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
        return RedirectResponse(ROUND_ROUTE, status_code=303)

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

    async def get_artifact_index(request: Request) -> HTMLResponse:
        kind = request.path_params["kind"]
        if kind not in KIND_LABELS:
            return HTMLResponse("Unknown artifact kind", status_code=404)
        items = discover_by_kind(planning)[kind]
        page = html_pages.artifact_index_page(kind, items, EMPTY_HELP[kind])
        return HTMLResponse(page)

    async def get_artifact_view(request: Request) -> HTMLResponse:
        rel = request.query_params.get("path", "")
        target = resolve_safe_path(planning, rel)
        if target is None or not target.is_file():
            return HTMLResponse(
                html_pages.error_page("Not found", [f"Cannot read {rel}"]),
                status_code=404,
            )
        try:
            text = target.read_text(encoding="utf-8")
        except OSError as exc:
            return HTMLResponse(
                html_pages.error_page("Read error", [str(exc)]),
                status_code=500,
            )
        content_html, has_mermaid = markdown_to_view_html(text)
        return HTMLResponse(
            html_pages.artifact_view_page(rel, content_html, has_mermaid=has_mermaid)
        )

    async def get_edit_glossary(_: Request) -> HTMLResponse:
        path = planning / "GLOSSARY.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else "# Glossary\n\n## Language\n\n"
        form = parse_glossary_form(text)
        fields = {
            "title": form.title,
            "term": form.term,
            "definition": form.definition,
            "avoid": form.avoid,
        }
        return HTMLResponse(html_pages.glossary_edit_page(fields))

    async def post_preview_glossary(request: Request) -> HTMLResponse:
        form = await request.form()
        path = planning / "GLOSSARY.md"
        before = path.read_text(encoding="utf-8") if path.is_file() else ""
        gf = parse_glossary_form(before)
        gf.title = str(form.get("title", gf.title))
        gf.term = str(form.get("term", ""))
        gf.definition = str(form.get("definition", ""))
        gf.avoid = str(form.get("avoid", ""))
        after = render_glossary(gf, before)
        diff = unified_diff(before, after, "GLOSSARY.md")
        return HTMLResponse(html_pages.diff_preview_page("GLOSSARY.md", diff, after))

    async def get_edit_adr(request: Request) -> HTMLResponse:
        rel = request.query_params.get("path", "")
        return _edit_adr_page(planning, rel)

    async def post_preview_adr(request: Request) -> HTMLResponse:
        form = await request.form()
        rel = str(form.get("path", ""))
        target = resolve_safe_path(planning, rel)
        if target is None:
            return HTMLResponse("Invalid path", status_code=400)
        title = str(form.get("title", "")).strip()
        body = str(form.get("body", "")).strip()
        if not title or not body:
            return HTMLResponse(
                html_pages.error_page(
                    "Invalid ADR",
                    ["Title and body are required."],
                ),
                status_code=400,
            )
        before = target.read_text(encoding="utf-8")
        af = parse_adr_form(before)
        af.title = title
        af.body = body
        after = render_adr(af)
        diff = unified_diff(before, after, rel)
        return HTMLResponse(html_pages.diff_preview_page(rel, diff, after))

    async def get_edit_spec(request: Request) -> HTMLResponse:
        rel = request.query_params.get("path", "")
        return _edit_spec_page(planning, rel)

    async def post_preview_spec(request: Request) -> HTMLResponse:
        form = await request.form()
        rel = str(form.get("path", ""))
        target = resolve_safe_path(planning, rel)
        if target is None:
            return HTMLResponse("Invalid path", status_code=400)
        before = target.read_text(encoding="utf-8")
        sf = parse_spec_form(before)
        sf.title = str(form.get("title", sf.title))
        sf.problem = str(form.get("problem", ""))
        sf.solution = str(form.get("solution", ""))
        after = render_spec(sf, before)
        diff = unified_diff(before, after, rel)
        return HTMLResponse(html_pages.diff_preview_page(rel, diff, after))

    async def get_edit_ticket(request: Request) -> HTMLResponse:
        rel = request.query_params.get("path", "")
        return _edit_ticket_page(planning, rel)

    async def post_preview_ticket(request: Request) -> HTMLResponse:
        form = await request.form()
        rel = str(form.get("path", ""))
        target = resolve_safe_path(planning, rel)
        if target is None:
            return HTMLResponse("Invalid path", status_code=400)
        before = target.read_text(encoding="utf-8")
        tf = parse_ticket_form(before)
        tf.title = str(form.get("title", tf.title))
        tf.what_to_build = str(form.get("what_to_build", ""))
        tf.acceptance = str(form.get("acceptance", ""))
        tf.blocked_by = str(form.get("blocked_by", ""))
        after = render_ticket(tf)
        diff = unified_diff(before, after, rel)
        return HTMLResponse(html_pages.diff_preview_page(rel, diff, after))

    async def post_edit_confirm(request: Request) -> HTMLResponse:
        form = await request.form()
        rel = str(form.get("path", ""))
        content = str(form.get("content", ""))
        target = resolve_safe_path(planning, rel)
        if target is None:
            return HTMLResponse("Invalid path", status_code=400)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return RedirectResponse(f"/artifact?path={quote(rel)}", status_code=303)

    routes = [
        Mount("/static", StaticFiles(directory=STATIC_DIR), name="static"),
        Route("/", get_dashboard, methods=["GET"]),
        Route(ROUND_ROUTE, get_round, methods=["GET"]),
        Route(ROUND_SUBMIT_ROUTE, post_submit, methods=["POST"]),
        Route(ROUND_COMPLETE_ROUTE, post_complete, methods=["POST"]),
        Route("/artifacts/{kind}", get_artifact_index, methods=["GET"]),
        Route("/artifact", get_artifact_view, methods=["GET"]),
        Route("/edit/glossary", get_edit_glossary, methods=["GET"]),
        Route("/edit/glossary/preview", post_preview_glossary, methods=["POST"]),
        Route("/edit/adr", get_edit_adr, methods=["GET"]),
        Route("/edit/adr/preview", post_preview_adr, methods=["POST"]),
        Route("/edit/spec", get_edit_spec, methods=["GET"]),
        Route("/edit/spec/preview", post_preview_spec, methods=["POST"]),
        Route("/edit/ticket", get_edit_ticket, methods=["GET"]),
        Route("/edit/ticket/preview", post_preview_ticket, methods=["POST"]),
        Route("/edit/confirm", post_edit_confirm, methods=["POST"]),
    ]
    return Starlette(routes=routes)


def _edit_adr_page(planning: Path, rel: str) -> HTMLResponse:
    target = resolve_safe_path(planning, rel)
    if target is None or not target.is_file():
        return HTMLResponse(html_pages.error_page("Not found", [rel]), status_code=404)
    af = parse_adr_form(target.read_text(encoding="utf-8"))
    return HTMLResponse(
        html_pages.adr_edit_page(rel, {"title": af.title, "body": af.body})
    )


def _edit_spec_page(planning: Path, rel: str) -> HTMLResponse:
    target = resolve_safe_path(planning, rel)
    if target is None or not target.is_file():
        return HTMLResponse(html_pages.error_page("Not found", [rel]), status_code=404)
    sf = parse_spec_form(target.read_text(encoding="utf-8"))
    return HTMLResponse(
        html_pages.spec_edit_page(
            rel,
            {"title": sf.title, "problem": sf.problem, "solution": sf.solution},
        )
    )


def _edit_ticket_page(planning: Path, rel: str) -> HTMLResponse:
    target = resolve_safe_path(planning, rel)
    if target is None or not target.is_file():
        return HTMLResponse(html_pages.error_page("Not found", [rel]), status_code=404)
    tf = parse_ticket_form(target.read_text(encoding="utf-8"))
    return HTMLResponse(
        html_pages.ticket_edit_page(
            rel,
            {
                "title": tf.title,
                "what_to_build": tf.what_to_build,
                "acceptance": tf.acceptance,
                "blocked_by": tf.blocked_by,
            },
        )
    )


def _active_round_response(
    workspace: Path, planning: Path, manifest: SessionManifest
) -> HTMLResponse:
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
    ctx = _context_panel(planning)
    return HTMLResponse(
        html_pages.active_round_page(prompt, history, context_panel=ctx)
    )


def _context_panel(planning: Path) -> str:
    glossary = planning / "GLOSSARY.md"
    if not glossary.is_file():
        return "<strong>Context</strong><p>No GLOSSARY.md yet.</p>"
    text = glossary.read_text(encoding="utf-8")
    snippet = text[:800] + ("..." if len(text) > 800 else "")
    return (
        "<strong>Context</strong>"
        f'<p><a href="/artifacts/glossary">Glossary</a></p>'
        f'<pre class="md-plain">{html.escape(snippet)}</pre>'
    )


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
