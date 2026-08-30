from pathlib import Path

import librosa
import numpy as np
import pytest
import scipy

from genre_test.retrieval import mfcc_baseline
from genre_test.retrieval.mfcc_baseline import (
    EMBEDDING_DIM,
    MFCCBaselineExtractor,
    SAMPLE_RATE,
    TARGET_RMS,
    extract_mfcc78,
    mfcc_baseline_info,
)


def _synthetic_audio(seconds: float = 2.0) -> np.ndarray:
    t = np.arange(int(SAMPLE_RATE * seconds), dtype=np.float32) / SAMPLE_RATE
    signal = (
        0.45 * np.sin(2.0 * np.pi * 110.0 * t)
        + 0.30 * np.sin(2.0 * np.pi * 220.0 * t)
        + 0.18 * np.sin(2.0 * np.pi * 440.0 * t)
        + 0.07 * np.sin(2.0 * np.pi * 1760.0 * t)
    )
    envelope = 0.75 + 0.25 * np.sin(2.0 * np.pi * 2.0 * t)
    return (signal * envelope).astype(np.float32)


def test_extract_mfcc78_is_float32_normalized_and_deterministic() -> None:
    audio = _synthetic_audio()

    first = extract_mfcc78(audio)
    second = extract_mfcc78(audio.copy())

    assert first.shape == (EMBEDDING_DIM,)
    assert first.dtype == np.float32
    assert np.all(np.isfinite(first))
    assert np.linalg.norm(first) == pytest.approx(1.0, abs=1e-6)
    np.testing.assert_array_equal(first, second)


def test_extract_mfcc78_is_stable_under_global_gain_changes() -> None:
    audio = _synthetic_audio()

    reference = extract_mfcc78(audio)
    quieter = extract_mfcc78(audio * 0.25)
    louder = extract_mfcc78(audio * 2.0)

    np.testing.assert_allclose(reference, quieter, rtol=2e-5, atol=2e-6)
    np.testing.assert_allclose(reference, louder, rtol=2e-5, atol=2e-6)


def test_backend_identity_is_versioned_and_audio_only() -> None:
    info = mfcc_baseline_info()

    assert info.backend_name == "mfcc-timbre78"
    assert info.backend_version == "2"
    assert info.embedding_dim == EMBEDDING_DIM
    assert info.normalization == "l2"
    assert "mfcc20" in info.preprocessing_version
    assert f"rms{TARGET_RMS:g}" in info.preprocessing_version
    assert f"librosa-{librosa.__version__}" in info.preprocessing_version
    assert f"numpy-{np.__version__}" in info.preprocessing_version
    assert f"scipy-{scipy.__version__}" in info.preprocessing_version
    assert info.clamp_code_revision is None
    assert info.mert_model_id is None
    assert info.text_model_id is None
    assert len(info.fingerprint) == 64


def test_embed_audio_preserves_full_track_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    audio = _synthetic_audio()

    def fake_load_audio(path: Path, sample_rate: int) -> tuple[np.ndarray, int]:
        assert path == Path("track.wav")
        assert sample_rate == SAMPLE_RATE
        return audio, SAMPLE_RATE

    monkeypatch.setattr(mfcc_baseline, "load_audio", fake_load_audio)

    vector = MFCCBaselineExtractor().embed_audio(Path("track.wav"), track_id="track-1")

    assert vector.dimension == EMBEDDING_DIM
    assert vector.identity.scope == "full"
    assert vector.identity.track_id == "track-1"
    assert vector.identity.start_s is None
    assert vector.identity.end_s is None


def test_embed_audio_preserves_segment_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    audio = _synthetic_audio(seconds=3.0)

    monkeypatch.setattr(
        mfcc_baseline,
        "load_audio",
        lambda _path, sample_rate: (audio, sample_rate),
    )

    vector = MFCCBaselineExtractor().embed_audio(
        Path("track.wav"),
        track_id="track-2",
        start_s=0.5,
        end_s=2.5,
    )

    assert vector.dimension == EMBEDDING_DIM
    assert vector.identity.scope == "segment"
    assert vector.identity.track_id == "track-2"
    assert vector.identity.start_s == 0.5
    assert vector.identity.end_s == 2.5


@pytest.mark.parametrize(
    ("start_s", "end_s", "match"),
    [
        (0.1, None, "provided together"),
        (None, 1.0, "provided together"),
        (-0.1, 1.0, "segment bounds"),
        (1.0, 1.0, "segment bounds"),
        (0.0, 4.0, "exceeds audio duration"),
    ],
)
def test_embed_audio_rejects_invalid_segment_bounds(
    monkeypatch: pytest.MonkeyPatch,
    start_s: float | None,
    end_s: float | None,
    match: str,
) -> None:
    audio = _synthetic_audio(seconds=2.0)
    monkeypatch.setattr(
        mfcc_baseline,
        "load_audio",
        lambda _path, sample_rate: (audio, sample_rate),
    )

    with pytest.raises(ValueError, match=match):
        MFCCBaselineExtractor().embed_audio(
            Path("track.wav"),
            track_id="track-3",
            start_s=start_s,
            end_s=end_s,
        )


def test_extract_mfcc78_rejects_invalid_audio() -> None:
    with pytest.raises(ValueError, match="mono audio"):
        extract_mfcc78(np.zeros((2, 4096), dtype=np.float32))

    with pytest.raises(ValueError, match="too short"):
        extract_mfcc78(np.zeros(1024, dtype=np.float32))

    invalid = np.zeros(4096, dtype=np.float32)
    invalid[100] = np.nan
    with pytest.raises(ValueError, match="finite samples"):
        extract_mfcc78(invalid)

    with pytest.raises(ValueError, match="non-silent energy"):
        extract_mfcc78(np.zeros(4096, dtype=np.float32))
