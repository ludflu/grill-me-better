"""Minimal markdown rendering for question bodies."""

from __future__ import annotations

import html


def body_markdown_to_html(text: str) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return ""
    return "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in paragraphs)
