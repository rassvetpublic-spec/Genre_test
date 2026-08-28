from __future__ import annotations

import sys
from typing import Any

_ALIAS_MAP = {
    "retrieval-segment-status": "segment-status",
    "retrieval-segment-index": "segment-index",
    "retrieval-search-representative": "search-representative",
    "retrieval-search-segment": "search-segment",
    "retrieval-catalog-audit": "catalog-audit",
    "retrieval-retry-missing": "retry-missing",
    "retrieval-benchmark-run": "benchmark-run",
    "retrieval-exit-codes": "exit-codes",
}


def _make_stream_encoding_tolerant(stream: Any) -> None:
    """Avoid locale-codepage crashes while preserving the active console encoding.

    On Windows, Python may inherit cp1251 even inside Windows Terminal. Rich then writes
    Unicode through that stream and can fail on characters outside the active code page
    (for example, ``é``). Keep the current encoding so Cyrillic remains readable, but
    replace otherwise unencodable characters with Python backslash escapes instead of
    aborting the command after reports have already been generated.
    """

    reconfigure = getattr(stream, "reconfigure", None)
    if not callable(reconfigure):
        return
    try:
        reconfigure(errors="backslashreplace")
    except (OSError, ValueError):
        # Some redirected/custom streams expose reconfigure but do not allow changing it.
        pass


def _configure_stdio() -> None:
    _make_stream_encoding_tolerant(sys.stdout)
    _make_stream_encoding_tolerant(sys.stderr)


def main() -> None:
    _configure_stdio()
    if len(sys.argv) > 1:
        sys.argv[1] = _ALIAS_MAP.get(sys.argv[1].casefold(), sys.argv[1])
    from .cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
