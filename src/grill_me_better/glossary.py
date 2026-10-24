"""Parse and render GLOSSARY.md (Matt Pocock glossary shape)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TERM_PATTERN = re.compile(
    r"\*\*(.+?)\*\*:\s*\n(.*?)(?:\n_Avoid_:\s*(.*?))?(?=\n\*\*|\n##|\Z)",
    re.DOTALL,
)


@dataclass
class GlossaryTerm:
    name: str
    definition: str
    avoid: str = ""


@dataclass
class GlossaryDocument:
    title: str
    preamble: str = ""
    terms: list[GlossaryTerm] = field(default_factory=list)
    tail: str = ""


def parse_glossary(markdown: str) -> GlossaryDocument:
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Glossary"
    lang_match = re.search(r"^## Language\s*$", markdown, re.MULTILINE)
    if not lang_match:
        return GlossaryDocument(title=title, preamble=markdown, terms=[])
    preamble = markdown[: lang_match.start()].strip()
    if title_match:
        preamble = preamble.replace(title_match.group(0), "", 1).strip()
    after_lang = markdown[lang_match.end() :]
    next_section = re.search(r"^## ", after_lang, re.MULTILINE)
    language_body = after_lang[: next_section.start()] if next_section else after_lang
    tail = after_lang[next_section.start() :] if next_section else ""
    terms: list[GlossaryTerm] = []
    for match in TERM_PATTERN.finditer(language_body):
        terms.append(
            GlossaryTerm(
                name=match.group(1).strip(),
                definition=match.group(2).strip(),
                avoid=(match.group(3) or "").strip(),
            )
        )
    return GlossaryDocument(title=title, preamble=preamble, terms=terms, tail=tail.strip())


def render_glossary(doc: GlossaryDocument) -> str:
    parts = [f"# {doc.title.strip()}", ""]
    if doc.preamble.strip():
        parts.append(doc.preamble.strip())
        parts.append("")
    parts.append("## Language")
    parts.append("")
    for term in doc.terms:
        parts.append(_term_block(term))
    if doc.tail.strip():
        parts.append(doc.tail.strip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _term_block(term: GlossaryTerm) -> str:
    avoid = f"\n_Avoid_: {term.avoid}" if term.avoid.strip() else ""
    return f"**{term.name}**:\n{term.definition.strip()}{avoid}\n"
