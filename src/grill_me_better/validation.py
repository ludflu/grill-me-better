"""JSON Schema validation for round artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from grill_me_better.paths import schema_path


def _load_schema(filename: str) -> dict[str, Any]:
    return json.loads(schema_path(filename).read_text(encoding="utf-8"))


def validate_round_prompt(data: dict[str, Any]) -> list[str]:
    return _validate(_load_schema("round-prompt.schema.json"), data)


def validate_round_answers(data: dict[str, Any]) -> list[str]:
    return _validate(_load_schema("round-answers.schema.json"), data)


def validate_fixture_file(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return validate_round_prompt(data)


def _validate(schema: dict[str, Any], data: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        loc = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors


def validation_error_messages(exc: ValidationError) -> list[str]:
    return [f"{'.'.join(str(p) for p in exc.path) or '(root)'}: {exc.message}"]
