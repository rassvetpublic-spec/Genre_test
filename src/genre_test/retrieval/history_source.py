from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REQUIRED_COLUMNS = {
    "tracks": frozenset({"track_id", "last_path"}),
    "runs": frozenset({"track_id", "result_json", "analyzed_at"}),
}


@dataclass(frozen=True)
class HistorySourceFailure:
    """Stable structured failure payload for CLI and future local API adapters."""

    code: str
    path: str
    message: str
    missing_tables: tuple[str, ...] = ()
    missing_columns: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": "history_source_error",
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }
        if self.missing_tables:
            payload["missing_tables"] = list(self.missing_tables)
        if self.missing_columns:
            payload["missing_columns"] = list(self.missing_columns)
        return payload


class HistorySourceError(RuntimeError):
    """Raised when an explicitly selected analysis-history source is unusable."""

    def __init__(self, failure: HistorySourceFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure

    def to_dict(self) -> dict[str, Any]:
        return self.failure.to_dict()


def _failure(
    code: str,
    path: Path,
    message: str,
    *,
    missing_tables: tuple[str, ...] = (),
    missing_columns: tuple[str, ...] = (),
) -> HistorySourceError:
    return HistorySourceError(
        HistorySourceFailure(
            code=code,
            path=str(path),
            message=message,
            missing_tables=missing_tables,
            missing_columns=missing_columns,
        )
    )


def validate_explicit_history(path: Path) -> Path:
    """Validate an explicitly selected history DB without creating or mutating it.

    The connection uses SQLite read-only URI mode. In addition to the retrieval schema,
    a read-only quick integrity pass is required so page-level corruption cannot escape
    schema-only validation and fail later outside the stable source-error contract.
    """

    selected = Path(path)
    if not selected.is_file():
        raise _failure(
            "history_source_missing",
            selected,
            f"explicit analysis history does not exist: {selected}",
        )

    uri = f"{selected.resolve().as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            table_rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            tables = {str(row[0]) for row in table_rows}
            missing_tables = tuple(sorted(set(_REQUIRED_COLUMNS) - tables))
            if missing_tables:
                raise _failure(
                    "history_source_invalid_schema",
                    selected,
                    "explicit analysis history is missing required tables: "
                    + ", ".join(missing_tables),
                    missing_tables=missing_tables,
                )

            missing_columns: list[str] = []
            for table, required in _REQUIRED_COLUMNS.items():
                column_rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                columns = {str(row[1]) for row in column_rows}
                for column in sorted(required - columns):
                    missing_columns.append(f"{table}.{column}")
            if missing_columns:
                missing = tuple(missing_columns)
                raise _failure(
                    "history_source_invalid_schema",
                    selected,
                    "explicit analysis history is missing required columns: "
                    + ", ".join(missing),
                    missing_columns=missing,
                )

            quick_rows = connection.execute("PRAGMA quick_check").fetchall()
            quick_messages = tuple(str(row[0]) for row in quick_rows if row)
            if quick_messages != ("ok",):
                detail = "; ".join(quick_messages[:3]) or "unknown SQLite integrity failure"
                raise _failure(
                    "history_source_corrupt",
                    selected,
                    "explicit analysis history failed SQLite quick_check: " + detail,
                )
    except HistorySourceError:
        raise
    except sqlite3.Error as exc:
        raise _failure(
            "history_source_unreadable",
            selected,
            f"explicit analysis history is not a readable SQLite database: {selected}",
        ) from exc

    return selected


def resolve_history_source(*, explicit_path: Path | None, default_path: Path) -> Path:
    """Resolve retrieval history while preserving implicit default behavior.

    An explicit path fails closed. When no explicit path is supplied, the existing
    default history path is returned without pre-validation so legacy migration and
    creation behavior remains owned by the existing default-history workflow.
    """

    if explicit_path is None:
        return Path(default_path)
    return validate_explicit_history(explicit_path)
