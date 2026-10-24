# UI hub (v2) — specification

Extends Grill Me Better v1 (**local grill server**) with a **session dashboard**, **artifact tabs**, rendered Mermaid from repo markdown, and structured editing. Source problem note: `improve-ui.md`. v1 behavior remains in `docs/SPEC.md`.

## Problem Statement

Matt Pocock-style planning produces rich repo artifacts—glossary, ADRs, specs, local tickets, diagrams in markdown—but v1 only gives you a browser surface for the current **grill round**. Dependency and architecture diagrams stay as raw Mermaid in markdown, shared understanding lives partly in `.grill/` and partly in docs without a unified GUI, and there is no one place to browse (let alone edit) the artifacts the skills create. That makes it harder to see context while grilling and harder to iterate on docs without leaving the flow.

## Solution

Extend the existing **local grill server** (same Python package, same long-lived `serve` process, localhost-only, bundled static assets) into a **UI hub (v2)**:

- **Session-first** landing: a **session dashboard** merges **session manifest** / **grill workspace** state with repo planning artifacts for the active **grill session**.
- **Artifact tabs** discover files via fixed path **conventions** (not a separate manifest registry in v2) and list everything the Matt Pocock skill set typically writes—glossary, ADRs, specs, `.scratch` specs and issues, and placeholders for wayfinder, research, and prototype outputs where those paths exist.
- **Mermaid** in committed repo markdown (```mermaid fences) renders in the browser using a **bundled** client library (no CDN).
- **Grill rounds** remain the canonical interview surface; during an active **round**, use a **split view**: question form plus an optional context side panel (artifact peek), not full tab chrome drowning the **frontier**.
- **Structured editors** per artifact type land in phases after a read-only **tracer bullet**; first editor is **Glossary**, with **diff preview** before any write back to disk. No auto-git from the server.

## User Stories

1. As a developer planning in a repo, I want the localhost app to open on a **session dashboard**, so that I see **grill session** status and key artifacts in one place.
2. As a developer, I want the dashboard to reflect `.grill/` state (current **round**, phase, completion), so that I know whether I am answering, waiting on the agent, or confirming **session completion**.
3. As a developer, I want **artifact tabs** for glossary, ADRs, specs, and local tickets, so that I can browse what the skills produced without opening many files in the editor.
4. As a developer, I want tabs for wayfinder maps, research outputs, and prototypes when those paths exist, so that “all artifacts” is honest even if some tabs are empty in a given repo.
5. As a developer, I want Mermaid diagrams in repo markdown rendered interactively in the browser, so that dependency graphs are readable during planning.
6. As a developer, I want diagram rendering to use bundled assets only, so that the hub works offline and in locked-down environments (same rule as v1).
7. As a developer, I want diagram sources to be existing markdown in the repo, so that diagrams stay versioned with docs and agents do not need a separate drop protocol in v2.
8. As a developer, I want to open a markdown file from an artifact tab and see any Mermaid blocks rendered inline, so that one file is enough for text plus diagram.
9. As a developer, I want read-only browsing in the first vertical slice, so that we ship navigation and rendering before edit complexity.
10. As a developer, I want a structured **Glossary** editor as the first write surface, so that the most frequently updated artifact during grilling is easier to fix in the UI.
11. As a developer, I want a diff preview before saving glossary edits, so that I do not accidentally corrupt `GLOSSARY.md`.
12. As a developer, I want later structured editors for ADRs, spec bodies, and local ticket markdown, so that each artifact type gets appropriate fields—not one generic textarea.
13. As a developer, I want saves to write directly to repo files, so that the editor remains the source of truth on disk.
14. As a developer, I want the server never to commit git changes, so that I stay in control of version control.
15. As a developer, I want active **grill rounds** to use a split layout (form + optional context panel), so that I can peek at glossary or spec while answering the **frontier**.
16. As a developer, I want submitting a **round** unchanged from v1 semantics, so that **answer handoff** and `wait --round N` still work for agents.
17. As a developer, I want **session completion** still confirmed in the UI, so that the agent’s done signal on disk is unchanged.
18. As a developer, I want one `serve` process for the whole **grill session**, so that I do not restart when switching between dashboard, tabs, and rounds.
19. As a developer, I want `serve` to resume an incomplete **grill workspace**, so that hub features do not wipe in-progress interviews.
20. As a developer, I want artifact discovery by convention (known paths), so that agents do not maintain a separate artifact index in v2.
21. As a maintainer, I want v2 implemented inside the existing Python package, so that CLI and HTTP stay one deployable unit (ADR-0002 spirit).
22. As a maintainer, I want v1 grill-with-docs parity preserved for rounds and `.grill/` contracts, so that `/grill-me-better` choreography still applies.
23. As an agent, I want round prompts and answers unchanged on disk, so that I do not need new handoff formats for interviewing.
24. As an agent, I want chat to remain summaries only for questions, so that the browser stays canonical for reading the **frontier** (ADR-0003 spirit).
25. As a developer, I want empty tabs to explain what path convention is missing, so that I know how to create the artifact.
26. As a developer, I want the planning repo root to be the cwd when I run `serve`, so that relative paths resolve predictably.
27. As a developer, I want `.grill/` still gitignored, so that session files never commit accidentally.
28. As a developer, I want bundled CSS and JS kept minimal, so that v2 does not become a SPA build pipeline in the first slices.
29. As a developer, I want the hub to tolerate repos with only a subset of artifacts, so that small repos still work.
30. As a developer, I want broken or missing markdown files to show a clear error in the tab, so that I can fix paths or content.
31. As a developer, I want invalid Mermaid to show a readable error in the page, so that I am not stuck with a blank diagram.
32. As a developer, I want to navigate from the dashboard to the current **round** when phase is `active_round`, so that I do not hunt for the form URL.
33. As a developer, I want collapsed history of prior **rounds** still available during grilling, so that v1 behavior is not regressed.
34. As a developer, I want this spec in `docs/SPEC-ui-hub.md`, so that v1 `docs/SPEC.md` stays stable.
35. As a developer, I want implementation to follow the agreed build order (read-only hub + mermaid, then glossary editor, then other editors), so that each slice is demoable before the next starts.

## Implementation Decisions

### Relationship to v1

- **UI hub (v2)** extends the same **local grill server** process; no second app or port strategy beyond v1’s pick-free-port behavior.
- Preserve v1 **grill workspace** layout, JSON **round prompt** / **round answers** schemas, **wait command**, and **session completion** file semantics.
- ADR-0004 resume behavior applies to the combined app.

### Navigation and layout

- Default route is the **session dashboard** (session-first), not the raw round form.
- **Active round**: split view—primary column is the v1-equivalent form; secondary column is an optional context panel (read-only artifact snippet or link list), user-dismissible or collapsible.
- **Artifact tabs** live in a consistent shell (shared header or nav) on dashboard and browse views; when entering focused **round** mode, chrome may simplify but split context remains available per above.
- **Session completion** and post-complete states reuse v1 completion UX, reachable from dashboard when phase is `awaiting_completion`.

### Artifact discovery (conventions)

Discover at planning repo root (process cwd unless overridden by an injectable root for tests):

| Kind | Convention |
| --- | --- |
| Glossary | `GLOSSARY.md` at repo root |
| ADRs | `docs/adr/*.md` (numeric prefix sort) |
| Specs | `docs/SPEC*.md`, `.scratch/*/spec.md` |
| Local tickets | `.scratch/*/issues/*.md` |
| Wayfinder | `.scratch/*/map.md` or existing wayfinder paths when present |
| Research | files under `docs/research/` or `.scratch/*/research*.md` when present |
| Prototypes | `.scratch/*/prototype*` or documented prototype paths when present |

Tabs may be hidden when a convention matches zero files, with helper text describing how to add the artifact.

### Mermaid rendering

- Parse markdown for fenced ```mermaid blocks only (no remote fetch).
- Ship a vendored/bundled Mermaid build as static assets served by the same Starlette app; initialize client-side when a diagram container is in the DOM.
- Do not introduce CDN dependencies.

### Read vs edit phases

**Phase A (tracer bullet):** **Session dashboard** + read-only **artifact tabs** for all convention types above + at least one end-to-end Mermaid render from a real markdown file in the test fixture repo.

**Phase B:** Structured **Glossary** editor: load parseable glossary sections, edit in structured fields, on Save compute diff against on-disk file, show **preview-diff** UI, write only after confirm.

**Phase C:** Structured editors for ADR, spec markdown, ticket markdown (field shapes follow existing ADR/glossary/ticket templates in Matt Pocock skills); same diff-preview guardrail.

Round 1 selected “structured editors for all types in v1 of hub”; sequencing above defers editors after read-only hub without dropping the goal.

### Write safety

- All browser-initiated writes: show unified diff preview, explicit confirm, then atomic write to target path.
- No git operations from the server.

### Agent and CLI contract

- Unchanged: agent writes **round prompt**, updates **session manifest**, `grill-me-better serve`, open browser, `grill-me-better wait --round N`, read **round answers**.
- Hub routes are for humans browsing/editing; agents may still edit files directly—hub is not required for agent correctness.

### Session manifest extensions (if needed)

- Prefer deriving dashboard state from existing `phase`, `status`, `currentRound` before adding fields.
- If new fields are required (e.g. last-viewed tab), add optional keys to **session manifest** schema with backward-compatible defaults for v1-only workspaces.

## Testing Decisions

### Seam (single public surface)

Extend v1’s seam: **CLI + HTTP behavior** against (1) a temporary **grill workspace** and (2) a temporary **planning repo tree** with injectable roots via environment variables (never the developer’s real `.grill/` or production repo).

From outside the package boundary:

- `serve` with seeded manifest + planning tree returns 200 on dashboard; body includes session phase and links or labels for discovered artifacts.
- Read-only tab GET returns glossary or ADR content from fixture files; missing files return clear errors.
- Markdown fixture with Mermaid renders a diagram container and client init marker (assert presence of diagram region and mermaid source attribution, not internal JS call order).
- Active **round** split view: GET while `active_round` includes question text and context panel region.
- v1 regressions: round submit, invalid prompt, `wait --round N`, resume, completion—existing tests stay green.
- Phase B: glossary save flow shows diff preview on POST; confirmed save updates fixture `GLOSSARY.md` content.

Good tests assert HTTP status, user-visible text, and files on disk in temp roots—not private helpers, CSS class names, or full SVG geometry.

Prior art: `tests/test_seam.py` and pytest + Starlette TestClient in the `grill-me-better` package.

### Seams check (for implementer)

One seam only: **black-box HTTP + CLI against temp workspace + temp planning repo**. No unit-test explosion on template helpers unless required to unblock seam tests.

## Out of Scope

- Separate non-Python app or microservice for the hub.
- CDN-delivered Mermaid or other assets.
- Agent-generated diagram drop directories (v2 uses repo markdown only).
- Artifact manifest registry in `.grill/` (conventions only in v2).
- Multi-user auth, remote hosting, sync across machines.
- Auto-git commit, branch, or PR from the server.
- Full visual design system / component library; plain readable HTML remains acceptable.
- Replacing Cursor skills or changing grill-with-docs interview rules.
- Real-time collaborative editing.

## Further Notes

- Decisions recorded in `.grill/round-*.answers.json` from the **grill session** on `improve-ui.md` (2026-10-24).
- Domain terms: `GLOSSARY.md` (**UI hub (v2)**, **session dashboard**, **artifact tab**).
- Implementation target repository: `grill-me-better` Python package; this document is the planning-repo copy in `grill-me-better-spec`.
- After approval, break into tickets with `/to-tickets` referencing this spec.
