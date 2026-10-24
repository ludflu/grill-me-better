---
name: grill-me-better
description: Grill-with-docs in the browser — one frontier round at a time with structured answer handoff from disk.
disable-model-invocation: true
---

Run a **grill session** like `grill-with-docs`, but the canonical question surface is the **local grill server**, not the terminal.

Call the Skill tool for the forked skills in this repo (not upstream mattpocock paths):

- `grill-me-better-grilling` — interview rounds as JSON **round prompts**
- `grill-me-better-domain-modeling` — glossary and ADRs (same gates as upstream)
- `grill-me-better-grill-with-docs` — orchestration glue

## Agent choreography (every round)

1. Compute the **frontier** and build a **round prompt** JSON object (see `docs/grill-me-better/SPEC.md`). Write it to `.grill/round-NNN.prompt.json` (three-digit `NNN`, same number as `"round"` in the file).
2. Update `.grill/session.json`: set `currentRound`, `status` to `waiting_for_answers`, `phase` to `active_round`. When the frontier is empty after processing answers, set `phase` to `awaiting_completion` instead of writing another prompt.
3. From the repository root, start the server once per **grill session** (background): `uv run grill-me-better serve`. On later rounds, do not start a second server if one is already running; `serve` **resumes** an incomplete workspace.
4. Read `port` from `.grill/session.json` and open the browser (macOS): `open "http://127.0.0.1:<port>/"`.
5. Block on **answer handoff**: `uv run grill-me-better wait --round N` (same `N` as the prompt). Exit means `.grill/round-NNN.answers.json` exists.
6. Read **round answers** from that file. Post only a **short summary** in chat — never paste the full question list (ADR-0003).
7. Repeat from step 1 until the frontier is empty, then wait for **session completion** in the UI (`.grill/session.complete.json` and `phase: complete` in the manifest) before spec or implementation work.

## Paths

| Artifact | Path |
| --- | --- |
| **Grill workspace** | `.grill/` (gitignored) |
| **Session manifest** | `.grill/session.json` |
| **Round prompt** | `.grill/round-NNN.prompt.json` |
| **Round answers** | `.grill/round-NNN.answers.json` |
| **Session completion** | `.grill/session.complete.json` |

Upstream Matt Pocock skills are forked under `skills/grill-me-better/` with attribution in `skills/grill-me-better/UPSTREAM.md`.
