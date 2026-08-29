from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ContractError


_SCHEMA_DIR = Path(__file__).resolve().with_name("contracts")


def load_schema(name: str) -> dict[str, Any]:
    path = _SCHEMA_DIR / f"{name}.schema.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"Schema not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"Invalid JSON schema {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"Schema root must be an object: {path}")
    return value


def validate_contract(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        _validate_type(value, expected_type, path)

    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{path}: {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ContractError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ContractError(f"{path}: unexpected properties {unknown!r}")

        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                validate_contract(child, child_schema, f"{path}.{key}")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_contract(item, schema["items"], f"{path}[{index}]")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            raise ContractError(f"{path}: string length is below {min_length}")

    if _is_number(value):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise ContractError(f"{path}: {value} is below minimum {minimum}")
        if maximum is not None and value > maximum:
            raise ContractError(f"{path}: {value} is above maximum {maximum}")


def _validate_type(value: Any, expected: str, path: str) -> None:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "number": _is_number,
        "integer": lambda item: type(item) is int,
        "boolean": lambda item: type(item) is bool,
        "null": lambda item: item is None,
    }
    checker = checks.get(expected)
    if checker is None:
        raise ContractError(f"{path}: unsupported schema type {expected!r}")
    if not checker(value):
        raise ContractError(
            f"{path}: expected {expected}, got {type(value).__name__}"
        )


def _is_number(value: Any) -> bool:
    return type(value) in (int, float)
