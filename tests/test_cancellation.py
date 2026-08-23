import pytest

from genre_test.cancellation import AnalysisCancelled, check_cancel


def test_check_cancel_is_noop_without_request():
    check_cancel(None)
    check_cancel(lambda: False)


def test_check_cancel_raises_on_request():
    with pytest.raises(AnalysisCancelled):
        check_cancel(lambda: True)
