# Round prompts are JSON on disk; chat is a summary only

During a grill session, the full text of each frontier round lives in `.grill/round-N.prompt.json` for the local server to render. The agent posts only a short summary in the terminal chat, not the full question list.

Terminal scrolling was the original problem; duplicating every question in chat would preserve that failure mode. The browser is the place to read and answer; chat remains the coordination channel for errors, summaries, and what to do next.
