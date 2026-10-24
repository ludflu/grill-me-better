"""Unified diff for save previews."""

from __future__ import annotations

import difflib


def unified_diff(before: str, after: str, path: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)",
    )
    return "".join(lines) or "(no changes)"
