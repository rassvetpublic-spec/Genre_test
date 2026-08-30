import numpy as np
import pytest

from genre_test.technical.temporal_structure import (
    ALGORITHM_ID,
    TemporalStructureConfig,
    analyze_temporal_structure,
)


def _click_track(*, sr=22050, duration=8.0, jitter=None, amplitudes=None):
    y = np.zeros(int(sr * duration), dtype=np.float32)
    times = np.arange(0.5, duration, 0.5)
    if jitter is not None:
        times = times + np.asarray(jitter, dtype=np.float64)
    if amplitudes is None:
        amplitudes = np.ones(times.size, dtype=np.float64)
    click = np.hanning(256).astype(np.float32)
    for t, amplitude in zip(times, amplitudes, strict=True):
        start = round(float(t) * sr)
        y[start : start + click.size] += float(amplitude) * click
    return y


def test_temporal_structure_is_deterministic_and_neutral():
    audio = _click_track()
    first = analyze_temporal_structure(audio, 22050).to_dict()
    second = analyze_temporal_structure(audio, 22050).to_dict()

    assert first == second
    assert first["schema"] == "temporal-structure-profile/1"
    assert first["algorithm_identity"] == ALGORITHM_ID
    serialized_keys = " ".join(
        str(key).lower()
        for section in first.values()
        if isinstance(section, dict)
        for key in section
    )
    assert "ai_probability" not in serialized_keys
    assert "suno" not in serialized_keys


def test_jittered_clicks_increase_ioi_variation():
    regular = analyze_temporal_structure(_click_track(), 22050)
    jitter = [
        0.00,
        0.04,
        -0.03,
        0.05,
        -0.04,
        0.02,
        -0.05,
        0.03,
        -0.02,
        0.045,
        -0.035,
        0.025,
        -0.045,
        0.035,
        -0.025,
    ]
    irregular = analyze_temporal_structure(_click_track(jitter=jitter), 22050)

    assert irregular.rhythm["inter_onset_interval_cv"] > regular.rhythm[
        "inter_onset_interval_cv"
    ]
    for profile in (regular, irregular):
        assert profile.rhythm["onset_grid_deviation_ms_median"] is not None
        assert profile.rhythm["onset_grid_deviation_ms_median"] >= 0.0
        assert profile.rhythm["onset_grid_deviation_ms_iqr"] is not None
        assert profile.rhythm["onset_grid_deviation_ms_iqr"] >= 0.0
        assert profile.rhythm["beat_locked_onset_ratio"] is not None
        assert 0.0 <= profile.rhythm["beat_locked_onset_ratio"] <= 1.0


def test_transient_energy_diversity_tracks_amplitude_changes():
    count = len(np.arange(0.5, 8.0, 0.5))
    regular = analyze_temporal_structure(_click_track(), 22050)
    varied = analyze_temporal_structure(
        _click_track(amplitudes=np.linspace(0.2, 1.0, count)), 22050
    )

    assert regular.transients["attack_similarity_median"] > 0.99
    assert varied.transients["attack_energy_cv"] > regular.transients["attack_energy_cv"]


def test_accepts_channels_first_and_channels_last():
    mono = _click_track(duration=3.0)
    channels_first = np.stack([mono, mono * 0.8])
    channels_last = channels_first.T

    a = analyze_temporal_structure(channels_first, 22050)
    b = analyze_temporal_structure(channels_last, 22050)

    assert a.duration_s == pytest.approx(3.0)
    assert b.duration_s == pytest.approx(3.0)
    assert a.rhythm["onset_count"] == b.rhythm["onset_count"]


def test_invalid_input_fails_explicitly():
    with pytest.raises(ValueError):
        analyze_temporal_structure(np.array([], dtype=np.float32), 22050)
    with pytest.raises(ValueError):
        analyze_temporal_structure(np.zeros(100, dtype=np.float32), 0)
    with pytest.raises(ValueError):
        analyze_temporal_structure(
            np.zeros(1000, dtype=np.float32),
            22050,
            config=TemporalStructureConfig(grid_subdivisions_per_beat=0),
        )
