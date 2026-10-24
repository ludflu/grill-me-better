# Resume an incomplete `.grill/` session instead of wiping it

If `.grill/session.json` exists and the session is not complete, `serve` resumes that grill session (same history and round state) rather than deleting the workspace and starting fresh.

Wiping would lose in-progress answers when the server restarts or the user re-runs the skill mid-session. Starting fresh requires an explicit “new session” path (documented later), not the default when a workspace already exists.
