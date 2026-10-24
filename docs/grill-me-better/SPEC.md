# Grill Me Better — v1 specification

## Problem

Matt Pocock’s `grill-with-docs` interview is right for thoughtful planning, but dumping whole frontier rounds into the terminal fights careful decisions. v1 keeps the same interview and domain-modeling behavior, with one round at a time in a local browser UI.

## Goals (v1)

- **Parity** with `grill-with-docs`: forked `grilling` + `domain-modeling` + orchestration, writing `GLOSSARY.md` and ADRs as terms/decisions resolve.
- **One round at a time** in the browser; earlier rounds visible as read-only collapsed history.
- **Controls per question**: radio options when provided, recommended option pre-selected, always **Write your own** (`customAnswer` overrides radio).
- **No extra decision log** beyond glossary/ADR and structured round answers (same gap as upstream; hand off to `to-spec` for the rest).

## Non-goals (v1)

- Multi-user, auth, remote hosting, cross-machine session sync.
- `grill-me`, `wayfinder`, `to-questionnaire` (terminal-only upstream).
- Polished visual design (plain, readable HTML is enough).
- CDN-dependent assets (bundled/inline CSS only).

## Repository layout (target)

```
/
├── PRD.md
├── README.md
├── GLOSSARY.md
├── docs/
│   ├── SPEC.md
│   └── adr/
├── fixtures/                    # sample round-N.prompt.json for dev
├── schemas/                     # round.prompt.json JSON Schema
├── pyproject.toml               # Python package; uv
├── src/grill_me_better/         # server, CLI, templates (TBD layout)
└── skills/
    ├── README.md                # upstream attribution
    ├── grill-me-better/         # entry skill (/grill-me-better)
    ├── grilling/                # fork; JSON round output + chat summary
    ├── domain-modeling/         # fork; unchanged discipline
    └── grill-with-docs/         # fork; rewritten orchestration (or merged into entry)
```

## Fork strategy

- Vendor fork copies of Matt Pocock skills in `skills/`; adapt rather than runtime-depend on external install.
- Keep upstream attribution and license visible in `skills/README.md`.
- ADR: [0001-fork-matt-pocock-skills.md](./adr/0001-fork-matt-pocock-skills.md).

## Runtime

- **Python only** for local HTTP server and CLI (ADR [0002](./adr/0002-python-local-server.md)).
- Package managed with **`uv`**; agent/user runs e.g. `uv run grill-me-better serve`, `uv run grill-me-better wait --round N`.
- Bind **`127.0.0.1` only**; try port **8765**, then increment until free; record port in session manifest.

## Grill workspace (`.grill/`)

- Path: repo root, **gitignored**.
- **Session manifest**: `.grill/session.json` — port, current round, status (`waiting` | `answered` | `complete`, exact enum TBD at implement).
- **Per round**: `.grill/round-NNN.prompt.json`, `.grill/round-NNN.answers.json`.
- **Completion**: `.grill/session.complete.json` after user confirms shared understanding in UI.
- If manifest exists and session not complete, **`serve` resumes** (ADR [0004](./adr/0004-resume-incomplete-grill-workspace.md)).

## Agent ↔ UI contract

1. User invokes **`/grill-me-better`** (single public entry; forked skills not invoked separately).
2. Agent applies grilling + domain-modeling rules; writes **full round** to `.grill/round-N.prompt.json` (ADR [0003](./adr/0003-prompt-json-canonical-ui.md)).
3. Agent posts **short summary** in chat only (not full questions).
4. Agent starts **`serve`** (background, one process per session).
5. Agent **opens browser** to session URL on each new round (macOS: `open`; document cross-platform if needed later).
6. Agent runs **`wait --round N`**; blocks until answers file exists — chat is not the submit signal.
7. Agent reads answers, updates glossary/ADRs inline, computes next frontier; repeat until empty.
8. UI shows final **Shared understanding confirmed** → writes `session.complete.json`; agent must read before spec/implement.

## Prompt / answers JSON (behavioral)

- Prompt validated against committed JSON Schema; invalid prompt → error page with validation messages.
- Every question: `options[]`, `recommendedOptionId`, submit may include `customAnswer` that overrides selected option.
- Exact field names and schema live in `schemas/` at implement time; must support markdown-ish question bodies and titles per grilling format.

## Cursor skill changes

- **`grilling`**: require structured prompt file + minimal chat summary each round.
- **`domain-modeling`**: same gates and file locations as upstream.
- **Entry skill**: documents the serve / wait / open-browser loop and paths under `.grill/`.

## v1 acceptance

- README: `uv sync`, `serve`, `wait`, Cursor skill install, happy path for one round.
- Fixtures: at least one sample `round-001.prompt.json` for UI dev without Cursor.
- Manual e2e: start session, render round, submit, agent can read answers and proceed (can be documented walkthrough with mock agent steps).

## After v1

- Explicit “new session” / wipe workspace command.
- Optional: terminal fallback if server fails.
