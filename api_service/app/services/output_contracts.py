"""Validation and prompting helpers for API-key final-output contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, SchemaError


class OutputContractError(ValueError):
    """Raised when an administrator supplies an invalid JSON Schema."""


@dataclass(frozen=True)
class OutputValidationError(Exception):
    errors: list[dict[str, str]]


def validate_schema(schema: dict[str, Any] | None) -> None:
    """Reject invalid schemas at save time instead of during a live request."""
    if schema is None:
        return
    if not isinstance(schema, dict):
        raise OutputContractError("output_schema must be a JSON object")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise OutputContractError(f"invalid JSON Schema: {exc.message}") from exc


def output_contract_prompt(schema: dict[str, Any] | None) -> str | None:
    if schema is None:
        return None
    rendered = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return (
        "Final-output contract: your final answer MUST be one valid JSON value matching the "
        "following JSON Schema. Do not use Markdown fences, commentary, or any text before or "
        f"after the JSON. This applies only after completing any needed tool calls. Schema: {rendered}"
    )


def validate_final_output(content: str, schema: dict[str, Any] | None) -> None:
    """Ensure the OpenAI-compatible message content is valid contracted JSON."""
    if schema is None:
        return
    try:
        instance = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OutputValidationError([{"path": "$", "reason": f"invalid JSON: {exc.msg}"}]) from exc
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    if errors:
        raise OutputValidationError(
            [
                {
                    "path": "$" + "".join(f"[{item}]" if isinstance(item, int) else f".{item}" for item in error.absolute_path),
                    "reason": error.message,
                }
                for error in errors[:20]
            ]
        )
