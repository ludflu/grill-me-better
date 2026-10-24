# Grill Me Better (v1)

Local **grill server** and Cursor skill **`/grill-me-better`**: same interview as grill-with-docs, one **round** at a time in the browser.

Full specification: [SPEC.md](./SPEC.md). Domain language: [GLOSSARY.md](./GLOSSARY.md).

## Setup

```bash
uv sync
```

Install the entry skill from `skills/productivity/grill-me-better/` using your agent’s skill path (same as other skills in this repo).

## One-round happy path (manual)

From a repo root where you want to plan:

```bash
mkdir -p .grill
cp fixtures/round-001.prompt.json .grill/round-001.prompt.json
```

In another terminal:

```bash
uv run grill-me-better serve
```

Note the port in `.grill/session.json`, then open `http://127.0.0.1:<port>/` in a browser. Submit the form.

In a third terminal:

```bash
uv run grill-me-better wait --round 1
echo "Answers:" && cat .grill/round-001.answers.json
```

`wait` exits when the answers file exists — that is the **answer handoff** signal for agents.

## CLI

| Command | Purpose |
| --- | --- |
| `uv run grill-me-better serve` | Start or resume the **local grill server** (localhost only) |
| `uv run grill-me-better wait --round N` | Block until **round answers** for round `N` exist |

Tests: `uv run pytest`
