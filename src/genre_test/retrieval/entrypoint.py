from __future__ import annotations

import sys

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


def main() -> None:
    if len(sys.argv) > 1:
        sys.argv[1] = _ALIAS_MAP.get(sys.argv[1].casefold(), sys.argv[1])
    from .cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
