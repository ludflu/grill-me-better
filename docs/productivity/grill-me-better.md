## What it does

`grill-me-better` runs the same planning interview as [grill-with-docs](https://aihero.dev/skills-grill-with-docs), but each **frontier** round appears in a local browser UI instead of scrolling past in the terminal. Answers are written to `.grill/` on disk so the agent picks them up with `grill-me-better wait` instead of you pasting into chat.

The **UI hub** adds a session dashboard, artifact tabs (glossary, ADRs, specs, tickets), rendered Mermaid in markdown, and structured editors with diff preview before save.

## When to reach for it

Invoke **`/grill-me-better`** in a repo where you are planning a change and want grill-with-docs discipline with a browser-first question surface.

Use it instead of `/grill-with-docs` when terminal question walls are hurting careful decisions. Use `/grill-with-docs` only if you do not want the local server.

Run `grill-me-better serve` from the **planning repo root** (where `.grill/` lives). Open `/` for the dashboard and `/round` when answering the active round.

## Common questions

**How do I install the skill?** Symlink or copy `skills/productivity/grill-me-better` (and the forked skills under `skills/grill-me-better/`) into `~/.cursor/skills/` or `~/.agents/skills/`. Install the CLI with `uv tool install --editable /path/to/grill-me-better`.

**Port already in use?** Either use the running server (check `.grill/session.json`), stop the old process, or let `serve` pick the next free port and update the manifest.

**Where is the spec?** Package docs: [docs/grill-me-better/README.md](../grill-me-better/README.md) and [SPEC-ui-hub.md](../grill-me-better/SPEC-ui-hub.md).

## It's working if

- The browser shows one round at a time with radios, recommended default, and write-in override.
- After submit, `.grill/round-NNN.answers.json` exists and `grill-me-better wait --round N` exits.
- The agent posts only short summaries in chat, not the full question list.
- You can browse planning artifacts from the hub tabs without opening every file in the editor.
