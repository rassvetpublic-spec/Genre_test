from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .history_source import (
    HistorySourceError,
    HistorySourceFailure,
    validate_explicit_history,
)

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

_HISTORY_COMMANDS = {
    "status",
    "retrieval-index-status",
    "index",
    "retrieval-index",
    "rebuild",
    "retrieval-rebuild",
    "search-text",
    "retrieval-search-text",
    "search-audio",
    "retrieval-search-audio",
    "segment-status",
    "segment-index",
    "search-representative",
    "search-segment",
    "catalog-audit",
    "retry-missing",
    "benchmark-run",
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


def _history_command(argv: list[str]) -> bool:
    if not argv:
        return False
    command = argv[0].casefold()
    command = _ALIAS_MAP.get(command, command)
    return command in _HISTORY_COMMANDS


def _empty_history_error() -> HistorySourceError:
    return HistorySourceError(
        HistorySourceFailure(
            code="history_source_invalid_path",
            path="",
            message="explicit analysis history path must not be empty",
        )
    )


def explicit_history_paths(argv: list[str]) -> tuple[Path, ...]:
    """Extract explicit ``--history`` values only for commands that own the option."""

    if not _history_command(argv):
        return ()

    selected: list[Path] = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            break
        if token == "--history":
            if index + 1 < len(argv):
                value = argv[index + 1]
                # A single-dash value is a valid Click Path value (for example,
                # ``-missing.sqlite3``). Preserve long-option/missing-value handling for
                # Click instead of misclassifying another ``--option`` as a source path.
                if value != "--" and not value.startswith("--"):
                    selected.append(Path(value))
                    index += 2
                    continue
        elif token.startswith("--history="):
            value = token.partition("=")[2]
            if not value:
                raise _empty_history_error()
            selected.append(Path(value))
        index += 1
    return tuple(selected)


def validate_explicit_history_argv(argv: list[str]) -> tuple[Path, ...]:
    """Fail closed on valid-command explicit history sources before backend dispatch."""

    paths = explicit_history_paths(argv)
    for path in paths:
        validate_explicit_history(path)
    return paths


def main() -> None:
    _configure_stdio()
    if len(sys.argv) > 1:
        sys.argv[1] = _ALIAS_MAP.get(sys.argv[1].casefold(), sys.argv[1])

    from .cli import EXIT_SOURCE_ERROR
    from .cli import main as cli_main

    try:
        validate_explicit_history_argv(sys.argv[1:])
    except HistorySourceError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(EXIT_SOURCE_ERROR) from exc

    cli_main()


if __name__ == "__main__":
    main()
