from __future__ import annotations

import os
from pathlib import Path

from .contracts import RetrievalHealth

CLAMP3_PYTHON_ENV = "GENRE_TEST_CLAMP3_PYTHON"


def detect_retrieval_health(env: dict[str, str] | None = None) -> RetrievalHealth:
    """Probe the optional retrieval runtime without importing or downloading model code.

    This is intentionally conservative during the v0.5 compatibility spike:
    - no configured sidecar -> N/A;
    - configured path missing -> FAIL;
    - configured interpreter exists -> WARN until the real sidecar protocol handshake exists.
    """

    values = os.environ if env is None else env
    configured = values.get(CLAMP3_PYTHON_ENV, "").strip()
    if not configured:
        return RetrievalHealth(
            status="N/A",
            value="not configured",
            details=(
                "Optional CLaMP 3 retrieval runtime is not configured; "
                "ordinary Genre_test analysis remains available."
            ),
        )

    interpreter = Path(configured).expanduser()
    if not interpreter.exists():
        return RetrievalHealth(
            status="FAIL",
            value=str(interpreter),
            details=f"Configured retrieval interpreter does not exist ({CLAMP3_PYTHON_ENV}).",
        )
    if not interpreter.is_file():
        return RetrievalHealth(
            status="FAIL",
            value=str(interpreter),
            details="Configured retrieval interpreter path is not a file.",
        )

    return RetrievalHealth(
        status="WARN",
        value=str(interpreter),
        details=(
            "Retrieval interpreter is configured, but CLaMP 3/MERT protocol handshake "
            "is not implemented yet in the runtime-spike branch."
        ),
    )
