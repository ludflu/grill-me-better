# Python for the local grill server (v1)

The browser UI and local HTTP server for Grill Me Better v1 are implemented in Python only—no Node/TypeScript service in this repo.

Python matches the maintainer’s stack preference and keeps the agent’s run instructions aligned with `uv`/`python -m` workflows already used elsewhere. Node would have been a slightly smoother default inside many JS-heavy repos, but v1 does not require shared tooling with application code; the server is a small, repo-local sidecar started during a grill session.
