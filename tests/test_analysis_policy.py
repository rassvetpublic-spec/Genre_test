from genre_test.analysis_policy import (
    duration_window_target,
    input_quality_for_duration,
    needs_more_auto_windows,
    spread_indices,
)


def test_duration_window_targets():
    assert duration_window_target(30.0) == 1
    assert duration_window_target(60.0) == 3
    assert duration_window_target(119.9) == 3
    assert duration_window_target(120.0) == 5
    assert duration_window_target(209.9) == 5
    assert duration_window_target(210.0) == 7
    assert duration_window_target(299.9) == 7
    assert duration_window_target(300.0) == 9
    assert duration_window_target(419.9) == 9
    assert duration_window_target(420.0) == 11


def test_input_quality_thresholds():
    quality, notes = input_quality_for_duration(2.0)
    assert quality == "INSUFFICIENT_AUDIO"
    assert notes

    quality, notes = input_quality_for_duration(9.99)
    assert quality == "INSUFFICIENT_AUDIO"
    assert notes

    quality, notes = input_quality_for_duration(10.0)
    assert quality == "SHORT_INPUT"
    assert notes

    quality, notes = input_quality_for_duration(29.99)
    assert quality == "SHORT_INPUT"
    assert notes

    assert input_quality_for_duration(30.0) == ("NORMAL", ())


def test_spread_indices_are_nested_over_final_grid():
    assert spread_indices(9, 5) == [0, 2, 4, 6, 8]
    assert spread_indices(7, 5) == [0, 2, 3, 4, 6]
    assert spread_indices(5, 5) == [0, 1, 2, 3, 4]


def test_auto_expands_only_when_result_is_not_stable_high_primary():
    assert not needs_more_auto_windows("primary", "high")
    assert needs_more_auto_windows("primary", "medium")
    assert needs_more_auto_windows("primary", "low-medium")
    assert needs_more_auto_windows("hybrid", "high")
    assert needs_more_auto_windows("hybrid", "low-medium")
