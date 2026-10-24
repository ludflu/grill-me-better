# Fork Matt Pocock skills instead of wrapping them

Grill Me Better v1 will vendor forked copies of the grilling, domain-modeling, and grill-with-docs skills inside this repo and adapt them for the browser UI, rather than depending on an external install of mattpocock-skills at runtime.

Forking trades easy upstream merges for full control over the orchestration skill (when to write round prompts, when to open the server, how handoff files are named) without fighting a one-line delegate skill or partial skill loading in Cursor. Wrapping would stay thinner but leaves behavior split across two repos and reproduces the “interview runs, file half silent” failure mode when dependencies do not load together.
