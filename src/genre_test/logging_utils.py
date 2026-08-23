from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path

from .runtime_meta import default_log_path

_LOCK = threading.Lock()


def append_log(message: str, *, path: Path | None = None) -> Path:
    target = (path or default_log_path()).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    text = message.rstrip()
    with _LOCK, target.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {text}\n")
    return target
