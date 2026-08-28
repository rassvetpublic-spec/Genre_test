import numpy as np

from genre_test.technical.mastering_metrics import (
    ALGORITHM_ID,
    correlation_lr,
    measure_mono_loss,
    measure_transient_retention,
    overall_mono_retention,
)


def _stereo(signal: np.ndarray) -> np.ndarray:
    return np.column_stack([signal, signal]).astype(np.float32)


def test_centered_stereo_has_zero_db_mono_retention() -> None:
    t = np.linspace(0.0, 1.0, 48000, endpoint=False)
    audio = _stereo(0.25 * np.sin(2.0 * np.pi * 440.0 * t))

    assert abs(float(overall_mono_retention(audio))) < 1e-9
    assert abs(float(correlation_lr(audio)) - 1.0) < 1e-9


def test_mono_loss_detects_added_antiphase_cancellation() -> None:
    sample_rate = 48000
    t = np.linspace(0.0, 1.0, sample_rate, endpoint=False)
    signal = 0.25 * np.sin(2.0 * np.pi * 220.0 * t)
    reference = _stereo(signal)
    candidate = np.column_stack([signal, -signal]).astype(np.float32)

    result = measure_mono_loss(
        reference,
        candidate,
        sample_rate,
        warn_db=-0.5,
        fail_db=-1.5,
    )

    assert result["status"] == "FAIL"
    assert result["worst_candidate_minus_reference_db"] < -100.0
    assert result["algorithm_id"] == ALGORITHM_ID


def test_transient_retention_fails_when_attack_window_is_reduced() -> None:
    sample_rate = 48000
    event = sample_rate // 2
    reference = np.zeros((sample_rate, 2), dtype=np.float32)
    candidate = np.zeros_like(reference)

    attack_start = event - int(0.005 * sample_rate)
    attack_stop = event + int(0.035 * sample_rate)
    sustain_start = event + int(0.045 * sample_rate)
    sustain_stop = event + int(0.145 * sample_rate)

    reference[attack_start:attack_stop] = 0.8
    reference[sustain_start:sustain_stop] = 0.2
    candidate[attack_start:attack_stop] = 0.4
    candidate[sustain_start:sustain_stop] = 0.2

    result, rows = measure_transient_retention(
        reference,
        candidate,
        sample_rate,
        [event],
        {"events_detected": 1, "selected_detector_scores_db": [8.0]},
        warn_db=-0.75,
        fail_db=-1.5,
    )

    assert result["status"] == "FAIL"
    assert result["events_used"] == 1
    assert result["attack_guard_delta_db"] < -1.5
    assert len(rows) == 1
