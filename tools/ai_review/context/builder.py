from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import uuid
from typing import Any

from ..schema import load_schema, validate_contract


def build_context(
    task: str,
    *,
    constraints: list[str] | None = None,
    artifacts: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    normalized_task = task.strip()
    if not normalized_task:
        raise ValueError("task must be a non-empty string")

    context = {
        "context_version": "1.0",
        "run_id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "task": normalized_task,
        "constraints": list(constraints or []),
        "artifacts": list(artifacts or []),
    }
    validate_contract(context, load_schema("context"))
    return context


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def context_sha256(context_json: str) -> str:
    return hashlib.sha256(context_json.encode("utf-8")).hexdigest()
