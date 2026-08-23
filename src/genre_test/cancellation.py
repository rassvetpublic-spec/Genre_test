from __future__ import annotations

from collections.abc import Callable

CancelCheck = Callable[[], bool]


class AnalysisCancelled(RuntimeError):
    """Raised when a cooperative cancellation request is observed."""


def check_cancel(cancel_check: CancelCheck | None) -> None:
    if cancel_check is not None and cancel_check():
        raise AnalysisCancelled("Operation cancelled by user")
