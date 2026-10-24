"""Markdown display helpers including Mermaid blocks."""

from __future__ import annotations

import html
import re

MERMAID_FENCE = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def markdown_to_view_html(text: str) -> tuple[str, bool]:
    has_mermaid = bool(MERMAID_FENCE.search(text))
    parts: list[str] = []
    last = 0
    for match in MERMAID_FENCE.finditer(text):
        before = text[last : match.start()]
        parts.append(_escape_preformatted(before))
        diagram = match.group(1).strip()
        parts.append(f'<pre class="mermaid">{html.escape(diagram)}</pre>')
        last = match.end()
    parts.append(_escape_preformatted(text[last:]))
    return "".join(parts), has_mermaid


def _escape_preformatted(text: str) -> str:
    if not text.strip():
        return ""
    return f"<pre class=\"md-plain\">{html.escape(text)}</pre>"
