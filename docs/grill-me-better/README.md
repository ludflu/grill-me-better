# Grill Me Better

Local **grill server** and Cursor skill **`/grill-me-better`**: grill-with-docs in the browser, plus a **UI hub** for planning artifacts.

- v1 spec: [SPEC.md](./SPEC.md) (in planning repos: `docs/SPEC-ui-hub.md` for hub v2)
- Domain language: [GLOSSARY.md](./GLOSSARY.md)

## Setup

```bash
uv sync
# or global CLI (recommended):
uv tool install --editable /path/to/grill-me-better
```

Install the entry skill from `skills/productivity/grill-me-better/` (or symlink into `~/.cursor/skills/` / `~/.agents/skills/`).

Run `serve` from the **planning repo root** (where `.grill/` and `GLOSSARY.md` live).

Optional environment variables:

| Variable | Purpose |
| --- | --- |
| `GRILL_WORKSPACE_ROOT` | Override `.grill/` location (tests) |
| `GRILL_PLANNING_ROOT` | Override planning repo root for artifact tabs (tests) |

## URLs (localhost)

| Path | Purpose |
| --- | --- |
| `/` | **Session dashboard** (phase, status, links) |
| `/round` | Active **grill round** (split view + context panel) |
| `/artifacts/{kind}` | Browse glossary, ADRs, specs, tickets, etc. |
| `/artifact?path=...` | Read markdown (Mermaid rendered when present) |
| `/edit/glossary`, `/edit/adr`, … | Structured editors with diff preview on save |

Open the dashboard after `serve`: `http://127.0.0.1:<port>/`. Open **`/round`** when the user should answer the **frontier**.

## One-round happy path (manual)

```bash
mkdir -p .grill
cp /path/to/grill-me-better/fixtures/round-001.prompt.json .grill/round-001.prompt.json
grill-me-better serve   # terminal 1 — note port in .grill/session.json
# browser: http://127.0.0.1:<port>/round — submit form
grill-me-better wait --round 1
cat .grill/round-001.answers.json
```

## CLI

| Command | Purpose |
| --- | --- |
| `grill-me-better serve` | Start or resume **local grill server** (127.0.0.1 only) |
| `grill-me-better wait --round N` | Block until **round answers** exist |

Tests: `uv run pytest`
