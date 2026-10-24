# Grill Me Better

A Cursor skill and local web UI that runs the same interview as grill-with-docs, one round at a time in the browser instead of the terminal.

## Language

**Grill session**:
A single planning interview in a repo, from the first frontier round until shared understanding is confirmed or the user stops.
_Avoid_: Chat, grilling chat

**Round**:
One batch of frontier questions the user answers together before the agent computes the next frontier.
_Avoid_: Wave, batch (unless referring to server batching)

**Frontier**:
The set of questions whose prerequisite decisions are already settled; the only questions asked in the current round.
_Avoid_: Open questions, backlog

**Round prompt**:
Structured description of the current round’s questions, written by the agent for the local server to render.
_Avoid_: Questionnaire file, form spec

**Round answers**:
Structured record of the user’s choices and write-ins for one round, produced by the UI and read by the agent to continue.
_Avoid_: Submission, response payload

**Answer handoff**:
The moment the agent reads round answers from disk after the user submits in the browser; no pasting answers into chat.
_Avoid_: Sync, callback

**Local grill server**:
The Python HTTP process started for one grill session; it serves the round UI and writes round answers into `.grill/`.
_Avoid_: Dev server, API server

**Grill workspace**:
The `.grill/` directory at the repo root holding session metadata, round prompts, and round answers for the active interview; gitignored.
_Avoid_: Cache dir, temp folder

**Session manifest**:
The `.grill/session.json` file recording port, current round, and session status for the active grill session.
_Avoid_: State file, config

**Wait command**:
A CLI subcommand that blocks until the answers file for the requested round exists; the agent runs it instead of using chat as the submit signal.
_Avoid_: Poll script, watch mode

**Session completion**:
The user confirming shared understanding in the UI, recorded as `.grill/session.complete.json`, after which the agent may proceed to spec or implementation.
_Avoid_: Done button, finish
