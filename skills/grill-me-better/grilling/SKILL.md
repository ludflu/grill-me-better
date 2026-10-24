---
name: grill-me-better-grilling
description: Browser-first grilling — frontier rounds as JSON round prompts, not terminal question walls.
---

Interview the user relentlessly until you reach shared understanding. Same **design tree** and **frontier** rules as upstream `grilling`, but each round is delivered through the **local grill server**.

## Round delivery (mandatory)

- Do **not** paste numbered frontier questions or recommended answers as the primary UI in chat.
- For each round, write a **round prompt** file under `.grill/` that validates against the committed JSON Schema in `schemas/round-prompt.schema.json`.
- Each question needs `id`, `title`, `bodyMarkdown` (multi-paragraph allowed), optional `options` (`id`, `label`), and `recommendedOptionId` when options exist.
- After writing the prompt, follow the serve → open browser → `wait --round N` loop documented in `/grill-me-better`.
- Read **round answers** from disk for the next frontier computation. Non-empty `customAnswer` on an answer overrides `selectedOptionId` for your interpretation.

## Chat

Post a brief summary after each **answer handoff** (decisions settled, surprises, what is blocked). Errors and coordination only — not a duplicate of the form.

## Completion

When the frontier is empty, set `phase` to `awaiting_completion` in `.grill/session.json` and tell the user to confirm shared understanding in the browser. Do not implement until **session completion** is on disk.

Finding facts is still your job (sub-agents, tools). Decisions are the user's.
