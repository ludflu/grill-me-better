"""Bootstrap and schema contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from grill_me_better.paths import package_root, round_prompt_path
from grill_me_better.validation import validate_fixture_file


def test_fixture_validates_against_round_prompt_schema() -> None:
    fixture = package_root() / "fixtures" / "round-001.prompt.json"
    assert validate_fixture_file(fixture) == []


def test_round_paths_use_zero_padded_numbers(tmp_path: Path) -> None:
    assert round_prompt_path(tmp_path, 1).name == "round-001.prompt.json"
    assert round_prompt_path(tmp_path, 12).name == "round-012.prompt.json"
