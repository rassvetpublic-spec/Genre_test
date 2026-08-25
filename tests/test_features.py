from __future__ import annotations

import warnings

import numpy as np

from genre_test.features import (
    _resolve_short_loop_tempo,
    extract_audio_features,
    extract_lightweight_audio_features,
)


def test_lightweight_features_are_warning_free_for_insufficient_audio() -> None:
    sr = 16000
    audio = np.zeros(sr * 2, dtype=np.float32)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        features = extract_audio_features(audio, sr)

    assert caught == []
    assert features.duration_s == 2.0
    assert features.bpm is None
    assert features.key is None
    assert features.mode is None
    assert features.rms == 0.0
    assert features.spectral_centroid_hz == 0.0
    assert features.spectral_rolloff_hz == 0.0
    assert features.zero_crossing_rate == 0.0


def test_lightweight_features_return_meaningful_basic_metrics() -> None:
    sr = 16000
    time = np.arange(sr * 2, dtype=np.float64) / sr
    audio = np.sin(2.0 * np.pi * 440.0 * time).astype(np.float32)

    features = extract_lightweight_audio_features(audio, sr)

    assert features.duration_s == 2.0
    assert features.bpm is None
    assert features.key is None
    assert features.mode is None
    assert 0.70 < features.rms < 0.71
    assert 430.0 < features.spectral_centroid_hz < 450.0
    assert 430.0 < features.spectral_rolloff_hz < 450.0
    assert features.zero_crossing_rate > 0.0


def test_short_loop_resolver_recovers_170_from_three_to_two_pulse() -> None:
    resolved = _resolve_short_loop_tempo(113.63636, 22.5882312925)
    assert abs(resolved - 170.0) < 0.01


def test_short_loop_resolver_does_not_force_weak_grid_match() -> None:
    assert _resolve_short_loop_tempo(120.0, 20.0) == 120.0


def test_long_audio_does_not_use_short_loop_grid_snap() -> None:
    assert _resolve_short_loop_tempo(113.63636, 180.0) == 113.63636
