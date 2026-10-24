"""Build glossary document from edit form POST."""

from __future__ import annotations

from typing import Any

from grill_me_better.glossary import GlossaryDocument, GlossaryTerm, parse_glossary


def document_from_form(form: Any, before: str) -> GlossaryDocument:
    existing = parse_glossary(before) if before.strip() else GlossaryDocument(title="Glossary")
    title = str(form.get("title", existing.title)).strip() or "Glossary"
    preamble = str(form.get("preamble", existing.preamble))
    count = int(form.get("term_count", len(existing.terms)) or 0)
    terms: list[GlossaryTerm] = []
    for index in range(count):
        name = str(form.get(f"name_{index}", "")).strip()
        if not name:
            continue
        terms.append(
            GlossaryTerm(
                name=name,
                definition=str(form.get(f"definition_{index}", "")).strip(),
                avoid=str(form.get(f"avoid_{index}", "")).strip(),
            )
        )
    new_name = str(form.get("new_name", "")).strip()
    if new_name:
        terms.append(
            GlossaryTerm(
                name=new_name,
                definition=str(form.get("new_definition", "")).strip(),
                avoid=str(form.get("new_avoid", "")).strip(),
            )
        )
    return GlossaryDocument(
        title=title,
        preamble=preamble,
        terms=terms,
        tail=existing.tail,
    )
