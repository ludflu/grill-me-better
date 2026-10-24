"""Structured editors for repo artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GlossaryForm:
    title: str
    intro: str
    term: str
    definition: str
    avoid: str


@dataclass
class AdrForm:
    title: str
    body: str


@dataclass
class SpecForm:
    title: str
    problem: str
    solution: str


@dataclass
class TicketForm:
    title: str
    what_to_build: str
    acceptance: str
    blocked_by: str


def parse_glossary_form(markdown: str) -> GlossaryForm:
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Glossary"
    intro = ""
    term = ""
    definition = ""
    avoid = ""
    term_match = re.search(
        r"\*\*(.+?)\*\*:\s*\n(.+?)(?:\n_Avoid_:\s*(.+))?(?=\n\*\*|\n##|\Z)",
        markdown,
        re.DOTALL,
    )
    if term_match:
        term = term_match.group(1).strip()
        definition = term_match.group(2).strip()
        avoid = (term_match.group(3) or "").strip()
    return GlossaryForm(title, intro, term, definition, avoid)


def render_glossary(form: GlossaryForm, original: str) -> str:
    if "**" in original and form.term:
        pattern = (
            rf"\*\*{re.escape(form.term)}\*\*:\s*\n.*?"
            rf"(?=\n\*\*|\n##|\Z)"
        )
        block = _glossary_term_block(form)
        if re.search(pattern, original, re.DOTALL):
            return re.sub(pattern, block, original, count=1, flags=re.DOTALL)
    header = f"# {form.title}\n\n## Language\n\n"
    return header + _glossary_term_block(form)


def _glossary_term_block(form: GlossaryForm) -> str:
    avoid_line = f"\n_Avoid_: {form.avoid}" if form.avoid else ""
    return f"**{form.term}**:\n{form.definition}{avoid_line}\n"


def parse_adr_form(markdown: str) -> AdrForm:
    lines = markdown.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "ADR"
    body = "\n".join(lines[1:]).strip()
    return AdrForm(title, body)


def render_adr(form: AdrForm) -> str:
    return f"# {form.title}\n\n{form.body.strip()}\n"


def parse_spec_form(markdown: str) -> SpecForm:
    title = _heading(markdown, 1) or "Spec"
    problem = _section(markdown, "Problem Statement") or _section(markdown, "Problem")
    solution = _section(markdown, "Solution")
    return SpecForm(title, problem, solution)


def render_spec(form: SpecForm, original: str) -> str:
    if "## Problem Statement" in original:
        out = re.sub(
            r"## Problem Statement\s*\n.*?(?=\n## )",
            f"## Problem Statement\n\n{form.problem.strip()}\n\n",
            original,
            count=1,
            flags=re.DOTALL,
        )
        out = re.sub(
            r"## Solution\s*\n.*?(?=\n## |\Z)",
            f"## Solution\n\n{form.solution.strip()}\n\n",
            out,
            count=1,
            flags=re.DOTALL,
        )
        return out
    return f"# {form.title}\n\n## Problem Statement\n\n{form.problem}\n\n## Solution\n\n{form.solution}\n"


def parse_ticket_form(markdown: str) -> TicketForm:
    title = _heading(markdown, 1) or "Ticket"
    what = _labeled_block(markdown, "What to build")
    acceptance = _checkbox_section(markdown, "Acceptance")
    blocked = _labeled_block(markdown, "Blocked by")
    return TicketForm(title, what, acceptance, blocked)


def render_ticket(form: TicketForm) -> str:
    criteria = form.acceptance.strip() or "- [ ] Criterion"
    blocked = form.blocked_by.strip() or "None (can start immediately)"
    return (
        f"# {form.title}\n\n"
        f"**What to build:** {form.what_to_build.strip()}\n\n"
        f"**Blocked by:** {blocked}\n\n"
        f"**Status:** ready-for-agent\n\n"
        f"{criteria}\n"
    )


def _heading(text: str, level: int) -> str | None:
    match = re.search(rf"^{'#' * level}\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"## {re.escape(name)}\s*\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _labeled_block(text: str, label: str) -> str:
    match = re.search(
        rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)",
        text,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _checkbox_section(text: str, keyword: str) -> str:
    if keyword.lower() not in text.lower():
        return ""
    idx = text.lower().find(keyword.lower())
    return text[idx:].strip()
