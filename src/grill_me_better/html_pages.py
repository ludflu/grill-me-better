"""HTML pages for the local grill server."""

from __future__ import annotations

import html
import json
from typing import Any

from grill_me_better.markdown_body import body_markdown_to_html


BASE_CSS = """
body { font-family: system-ui, sans-serif; max-width: 48rem; margin: 0 auto; padding: 0 1rem 2rem; }
nav.hub { border-bottom: 1px solid #ddd; margin-bottom: 1.5rem; padding: 0.75rem 0; }
nav.hub a { margin-right: 1rem; }
nav.hub a.active { font-weight: 700; }
main { max-width: 42rem; }
h1 { font-size: 1.25rem; }
fieldset { border: 1px solid #ccc; margin: 1rem 0; padding: 1rem; }
legend { font-weight: 600; }
label { display: block; margin: 0.35rem 0; }
textarea { width: 100%; min-height: 4rem; margin-top: 0.5rem; }
button { margin-top: 1rem; padding: 0.5rem 1rem; }
details { margin: 0.75rem 0; border: 1px solid #ddd; padding: 0.5rem 1rem; }
.error { color: #a00; }
ul.errors { background: #fee; padding: 1rem; }
"""


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def hub_shell(title: str, body: str, *, active: str) -> str:
    dash = "active" if active == "dashboard" else ""
    rnd = "active" if active == "round" else ""
    nav = (
        f'<nav class="hub" aria-label="Grill hub">'
        f'<a href="/" class="{dash}">Dashboard</a>'
        f'<a href="/round" class="{rnd}">Round</a>'
        f"</nav>"
    )
    return page(title, f"{nav}<main>{body}</main>")


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
        body = (
            "<h1>Session dashboard</h1>"
            f"<p>Phase: {html.escape(phase or 'unknown')}</p>"
            f"<p>Status: {html.escape(status or 'unknown')}</p>"
            f"<p>Current round: {current_round if current_round is not None else 'n/a'}</p>"
            '<p><a href="/round">Open active round</a></p>'
        )
    return hub_shell("Session dashboard", body, active="dashboard")


def error_page(title: str, messages: list[str]) -> str:
    items = "".join(f"<li>{html.escape(m)}</li>" for m in messages)
    body = f"<h1>{html.escape(title)}</h1><ul class=\"errors\">{items}</ul>"
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
    body = f"""
<h1>{round_title}</h1>
{history_html}
{err}
<form method="post" action="/round/submit">
{fields}
<button type="submit">Submit round</button>
</form>
"""
    return hub_shell(round_title, body, active="round")
