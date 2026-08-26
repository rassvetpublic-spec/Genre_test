from __future__ import annotations

import os
from pathlib import Path

from .contracts import RetrievalHealth

CLAMP3_PYTHON_ENV = "GENRE_TEST_CLAMP3_PYTHON"


def detect_retrieval_health(env: dict[str, str] | None = None) -> RetrievalHealth:
    """Probe optional retrieval configuration without importing heavy model code.

    This lightweight probe intentionally does not start CLaMP/MERT. It only reports
    whether the configured isolated interpreter exists. A live protocol/model check
    is performed by ``Clamp3SidecarBackend.health()`` when the retrieval backend is
    actually opened.
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
            "Retrieval interpreter is configured. This lightweight probe does not start "
            "the heavy runtime; use Clamp3SidecarBackend.health() for the live protocol/model check."
        ),
    )
