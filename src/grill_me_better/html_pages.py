"""HTML pages for the local grill server."""

from __future__ import annotations

import html
from typing import Any

from grill_me_better.artifacts import KIND_LABELS, ArtifactRef
from grill_me_better.glossary import GlossaryDocument, GlossaryTerm
from grill_me_better.markdown_body import body_markdown_to_html


BASE_CSS = """
body { font-family: system-ui, sans-serif; max-width: 56rem; margin: 0 auto; padding: 0 1rem 2rem; }
nav.hub { border-bottom: 1px solid #ddd; margin-bottom: 1.5rem; padding: 0.75rem 0; }
nav.hub a { margin-right: 0.75rem; font-size: 0.9rem; }
nav.hub a.active { font-weight: 700; }
main { max-width: 48rem; }
.split { display: flex; gap: 1rem; align-items: flex-start; }
.split .primary { flex: 2; min-width: 0; }
.split aside.context { flex: 1; border: 1px solid #ddd; padding: 0.75rem; font-size: 0.85rem; }
h1 { font-size: 1.25rem; }
fieldset { border: 1px solid #ccc; margin: 1rem 0; padding: 1rem; }
legend { font-weight: 600; }
label { display: block; margin: 0.35rem 0; }
textarea { width: 100%; min-height: 4rem; margin-top: 0.5rem; }
input[type=text] { width: 100%; }
button { margin-top: 1rem; padding: 0.5rem 1rem; margin-right: 0.5rem; }
details { margin: 0.75rem 0; border: 1px solid #ddd; padding: 0.5rem 1rem; }
.error { color: #a00; }
ul.errors { background: #fee; padding: 1rem; }
pre.md-plain { white-space: pre-wrap; background: #f8f8f8; padding: 0.75rem; }
pre.diff { white-space: pre-wrap; background: #f4f4f4; padding: 0.75rem; font-size: 0.8rem; }
ul.files { list-style: none; padding: 0; }
ul.files li { margin: 0.35rem 0; }
.glossary-view dl { margin: 1rem 0; }
.glossary-view dt { font-weight: 700; margin-top: 1rem; }
.glossary-view dd { margin: 0.25rem 0 0 0; }
.glossary-view .avoid { color: #555; font-size: 0.9rem; margin-top: 0.35rem; }
.glossary-edit fieldset.term { margin: 1rem 0; }
.glossary-edit textarea.description { min-height: 6rem; }
.glossary-edit .hint { color: #555; font-size: 0.9rem; margin: 0.5rem 0 1rem; }
"""


def page(title: str, body: str, *, extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}</style>
  {extra_head}
</head>
<body>
{body}
</body>
</html>"""


def _artifact_nav(active_kind: str | None = None) -> str:
    links = []
    for kind, label in KIND_LABELS.items():
        cls = "active" if active_kind == kind else ""
        links.append(f'<a href="/artifacts/{kind}" class="{cls}">{html.escape(label)}</a>')
    return "".join(links)


def hub_shell(
    title: str,
    body: str,
    *,
    active: str,
    artifact_kind: str | None = None,
    extra_head: str = "",
) -> str:
    dash = "active" if active == "dashboard" else ""
    rnd = "active" if active == "round" else ""
    art = "active" if active == "artifacts" else ""
    gloss = "active" if active == "glossary" else ""
    nav = (
        f'<nav class="hub" aria-label="Grill hub">'
        f'<a href="/" class="{dash}">Dashboard</a>'
        f'<a href="/round" class="{rnd}">Round</a>'
        f'<a href="/glossary" class="{gloss}">Glossary</a>'
        f'<span class="{art}">'
        f"{_artifact_nav(artifact_kind)}"
        f"</span>"
        f"</nav>"
    )
    return page(title, f"{nav}<main>{body}</main>", extra_head=extra_head)


def mermaid_head() -> str:
    return (
        '<script src="/static/mermaid.min.js"></script>'
        '<script src="/static/hub.js"></script>'
    )


def dashboard_page(
    *,
    has_session: bool,
    phase: str | None,
    status: str | None,
    current_round: int | None,
) -> str:
    if not has_session:
        body = (
            "<h1>Session dashboard</h1>"
            "<p>No grill session yet. Start <code>/grill-me-better</code> "
            "or add <code>.grill/session.json</code> and a round prompt.</p>"
        )
    else:
        round_link = ""
        if phase == "active_round":
            round_link = '<p><a href="/round">Open active round</a></p>'
        completion = ""
        if phase == "awaiting_completion":
            completion = '<p><a href="/round">Confirm shared understanding</a></p>'
        body = (
            "<h1>Session dashboard</h1>"
            f"<p>Phase: {html.escape(phase or 'unknown')}</p>"
            f"<p>Status: {html.escape(status or 'unknown')}</p>"
            f"<p>Current round: {current_round if current_round is not None else 'n/a'}</p>"
            f"{round_link}{completion}"
            "<p>Browse planning artifacts using the tabs above.</p>"
        )
    return hub_shell("Session dashboard", body, active="dashboard")


def artifact_index_page(kind: str, items: list[ArtifactRef], empty_help: str) -> str:
    if items:
        if kind == "glossary":
            body = (
                f"<h1>{html.escape(KIND_LABELS[kind])}</h1>"
                '<p><a href="/glossary">View and edit GLOSSARY.md</a></p>'
            )
            return hub_shell(KIND_LABELS[kind], body, active="artifacts", artifact_kind=kind)
        lis = "".join(
            f'<li><a href="/artifact?path={html.escape(i.rel_path, quote=True)}">'
            f"{html.escape(i.label)}</a></li>"
            for i in items
        )
        body = f"<h1>{html.escape(KIND_LABELS[kind])}</h1><ul class=\"files\">{lis}</ul>"
    else:
        body = (
            f"<h1>{html.escape(KIND_LABELS[kind])}</h1>"
            f"<p>No files found. {html.escape(empty_help)}</p>"
        )
    return hub_shell(KIND_LABELS[kind], body, active="artifacts", artifact_kind=kind)


def artifact_view_page(rel_path: str, content_html: str, *, has_mermaid: bool) -> str:
    edit = ""
    if rel_path == "GLOSSARY.md":
        edit = ' <a href="/glossary">View glossary</a>'
    elif rel_path.startswith("docs/adr/"):
        q = html.escape(rel_path, quote=True)
        edit = f' <a href="/edit/adr?path={q}">Edit ADR</a>'
    elif "spec" in rel_path.lower():
        q = html.escape(rel_path, quote=True)
        edit = f' <a href="/edit/spec?path={q}">Edit spec</a>'
    elif "/issues/" in rel_path:
        q = html.escape(rel_path, quote=True)
        edit = f' <a href="/edit/ticket?path={q}">Edit ticket</a>'
    head = mermaid_head() if has_mermaid else ""
    body = (
        f"<h1>{html.escape(rel_path)}</h1>{edit}"
        f'<div class="artifact-body">{content_html}</div>'
    )
    return hub_shell(rel_path, body, active="artifacts", extra_head=head)


def diff_preview_page(rel_path: str, diff_text: str, new_content: str) -> str:
    body = (
        f"<h1>Preview changes: {html.escape(rel_path)}</h1>"
        f"<pre class=\"diff\">{html.escape(diff_text)}</pre>"
        f'<form method="post" action="/edit/confirm">'
        f'<input type="hidden" name="path" value="{html.escape(rel_path)}">'
        f'<textarea name="content" hidden>{html.escape(new_content)}</textarea>'
        f'<button type="submit">Confirm save</button>'
        f"</form>"
    )
    return hub_shell("Preview diff", body, active="artifacts")


def glossary_page(doc: GlossaryDocument, *, creating: bool = False) -> str:
    hint = (
        '<p class="hint">No GLOSSARY.md yet — fill in terms below and save to create the file.</p>'
        if creating
        else '<p class="hint">Edit descriptions and other fields, then preview changes before saving.</p>'
    )
    rows = (
        f'<label>Title<input type="text" name="title" '
        f'value="{html.escape(doc.title)}"></label>'
        f'<label>Intro (before ## Language)<textarea name="preamble">'
        f"{html.escape(doc.preamble)}</textarea></label>"
        "<h2>Language</h2>"
    )
    for index, term in enumerate(doc.terms):
        rows += (
            f'<fieldset class="term"><legend>{html.escape(term.name)}</legend>'
            f'<input type="hidden" name="index" value="{index}">'
            f'<label>Term<input type="text" name="name_{index}" '
            f'value="{html.escape(term.name)}"></label>'
            f'<label>Description<textarea class="description" '
            f'name="definition_{index}">'
            f"{html.escape(term.definition)}</textarea></label>"
            f'<label>Avoid<textarea name="avoid_{index}">'
            f"{html.escape(term.avoid)}</textarea></label></fieldset>"
        )
    rows += (
        '<fieldset class="term"><legend>Add term</legend>'
        '<label>Term<input type="text" name="new_name"></label>'
        '<label>Description<textarea class="description" name="new_definition">'
        "</textarea></label>"
        '<label>Avoid<textarea name="new_avoid"></textarea></label></fieldset>'
        f'<input type="hidden" name="term_count" value="{len(doc.terms)}">'
        '<button type="submit">Preview diff</button>'
    )
    if doc.tail.strip():
        rows += (
            f'<p class="hint">Content after ## Language (read-only in this editor):</p>'
            f'<pre class="md-plain">{html.escape(doc.tail)}</pre>'
        )
    body = (
        f"<h1>{html.escape(doc.title)}</h1>"
        f"{hint}"
        f'<form class="glossary-edit" method="post" action="/edit/glossary/preview">'
        f"{rows}</form>"
    )
    return hub_shell(doc.title, body, active="glossary")


def adr_edit_page(path: str, form_fields: dict[str, str]) -> str:
    body = (
        f"<h1>Edit ADR</h1><p>{html.escape(path)}</p>"
        + _edit_form(
            "/edit/adr/preview",
            [
                ("title", "Title", form_fields.get("title", "")),
                ("body", "Body", form_fields.get("body", ""), True),
            ],
            hidden={"path": path},
        )
    )
    return hub_shell("Edit ADR", body, active="artifacts", artifact_kind="adr")


def spec_edit_page(path: str, form_fields: dict[str, str]) -> str:
    body = (
        f"<h1>Edit spec</h1><p>{html.escape(path)}</p>"
        + _edit_form(
            "/edit/spec/preview",
            [
                ("title", "Title", form_fields.get("title", "")),
                ("problem", "Problem", form_fields.get("problem", ""), True),
                ("solution", "Solution", form_fields.get("solution", ""), True),
            ],
            hidden={"path": path},
        )
    )
    return hub_shell("Edit spec", body, active="artifacts", artifact_kind="spec")


def ticket_edit_page(path: str, form_fields: dict[str, str]) -> str:
    body = (
        f"<h1>Edit ticket</h1><p>{html.escape(path)}</p>"
        + _edit_form(
            "/edit/ticket/preview",
            [
                ("title", "Title", form_fields.get("title", "")),
                ("what_to_build", "What to build", form_fields.get("what_to_build", ""), True),
                ("acceptance", "Acceptance criteria", form_fields.get("acceptance", ""), True),
                ("blocked_by", "Blocked by", form_fields.get("blocked_by", "")),
            ],
            hidden={"path": path},
        )
    )
    return hub_shell("Edit ticket", body, active="artifacts", artifact_kind="ticket")


def _edit_form(
    action: str,
    fields: list[tuple],
    *,
    hidden: dict[str, str] | None = None,
) -> str:
    rows = ""
    for item in fields:
        name, label, value = item[0], item[1], item[2]
        area = len(item) > 3 and item[3]
        if area:
            rows += (
                f"<label>{html.escape(label)}"
                f'<textarea name="{name}">{html.escape(value)}</textarea></label>'
            )
        else:
            rows += (
                f"<label>{html.escape(label)}"
                f'<input type="text" name="{name}" value="{html.escape(value)}"></label>'
            )
    hidden_fields = ""
    for k, v in (hidden or {}).items():
        hidden_fields += f'<input type="hidden" name="{k}" value="{html.escape(v)}">'
    return f'<form method="post" action="{action}">{hidden_fields}{rows}<button type="submit">Preview diff</button></form>'


def error_page(title: str, messages: list[str], *, hub: bool = True) -> str:
    items = "".join(f"<li>{html.escape(m)}</li>" for m in messages)
    body = f"<h1>{html.escape(title)}</h1><ul class=\"errors\">{items}</ul>"
    if hub:
        return hub_shell(title, body, active="dashboard")
    return page(title, body)


def answers_submitted_page(round_number: int) -> str:
    body = f"""
<h1>Round {round_number} submitted</h1>
<p>Your answers are on disk for the agent. You can close this tab until the next round opens.</p>
<p><a href="/">Back to dashboard</a></p>
"""
    return hub_shell("Answers submitted", body, active="round")


def completion_page() -> str:
    body = """
<h1>Confirm shared understanding</h1>
<p>The frontier is empty. Confirm when you are ready for the agent to proceed.</p>
<form method="post" action="/round/complete">
  <button type="submit">Shared understanding confirmed</button>
</form>
"""
    return hub_shell("Session completion", body, active="round")


def history_section(
    round_number: int,
    prompt: dict[str, Any],
    answers: dict[str, Any] | None,
) -> str:
    answer_by_q = {}
    if answers:
        answer_by_q = {a["questionId"]: a for a in answers.get("answers", [])}
    inner = ""
    for q in prompt.get("questions", []):
        ans = answer_by_q.get(q["id"], {})
        custom = (ans.get("customAnswer") or "").strip()
        selected = ans.get("selectedOptionId")
        if custom:
            display = html.escape(custom)
        elif selected:
            labels = {o["id"]: o["label"] for o in q.get("options", [])}
            display = html.escape(labels.get(selected, selected))
        else:
            display = "<em>(no answer)</em>"
        inner += f"<p><strong>{html.escape(q['title'])}</strong><br>{display}</p>"
    title = html.escape(prompt.get("title", f"Round {round_number}"))
    return f"<details><summary>{title}</summary>{inner}</details>"


def active_round_page(
    prompt: dict[str, Any],
    history_html: str,
    form_error: str | None = None,
    context_panel: str = "",
) -> str:
    round_title = html.escape(prompt.get("title", "Grill round"))
    fields = ""
    for q in prompt["questions"]:
        qid = html.escape(q["id"])
        fields += f"<fieldset><legend>{html.escape(q['title'])}</legend>"
        fields += body_markdown_to_html(q.get("bodyMarkdown", ""))
        options = q.get("options") or []
        recommended = q.get("recommendedOptionId")
        for opt in options:
            oid = html.escape(opt["id"])
            checked = " checked" if recommended == opt["id"] else ""
            fields += (
                f'<label><input type="radio" name="q_{qid}" '
                f'value="{oid}"{checked}> {html.escape(opt["label"])}</label>'
            )
        fields += (
            f'<label>Write your own<br>'
            f'<textarea name="custom_{qid}" placeholder="Optional override"></textarea></label>'
        )
        fields += "</fieldset>"
    err = f'<p class="error">{html.escape(form_error)}</p>' if form_error else ""
    aside = f'<aside class="context">{context_panel}</aside>' if context_panel else ""
    body = f"""
<div class="split">
<div class="primary">
<h1>{round_title}</h1>
{history_html}
{err}
<form method="post" action="/round/submit">
{fields}
<button type="submit">Submit round</button>
</form>
</div>
{aside}
</div>
"""
    return hub_shell(round_title, body, active="round")
