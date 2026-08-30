from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np
import scipy

from genre_test.audio import load_audio

from .contracts import EmbeddingIdentity, EmbeddingVector, RetrievalBackendInfo

SAMPLE_RATE = 22_050
N_FFT = 2_048
HOP_LENGTH = 512
N_MELS = 128
N_MFCC = 20
N_CHROMA = 12
N_CONTRAST_BANDS = 6  # librosa returns n_bands + 1 = 7 values
EMBEDDING_DIM = 78
TARGET_RMS = 0.1
EXTRACTOR_IMPLEMENTATION = (
    f"librosa-{librosa.__version__}-numpy-{np.__version__}-scipy-{scipy.__version__}"
)
PREPROCESSING_VERSION = (
    "mfcc20-chroma12-contrast7-meanstd-sr22050-mono-nfft2048-hop512-"
    f"rms{TARGET_RMS:g}-{EXTRACTOR_IMPLEMENTATION}-v2"
)


def mfcc_baseline_info() -> RetrievalBackendInfo:
    """Return the immutable identity of the model-free timbral baseline."""

    return RetrievalBackendInfo(
        backend_name="mfcc-timbre78",
        backend_version="2",
        clamp_code_revision=None,
        clamp_weight_name=None,
        clamp_weight_sha256=None,
        mert_model_id=None,
        mert_revision=None,
        text_model_id=None,
        text_model_revision=None,
        text_tokenizer_revision=None,
        preprocessing_version=PREPROCESSING_VERSION,
        embedding_dim=EMBEDDING_DIM,
        normalization="l2",
    )


def _normalize_analysis_level(samples: np.ndarray) -> np.ndarray:
    """Normalize RMS so global gain does not masquerade as timbral distance."""

    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64, copy=False)))))
    if not np.isfinite(rms) or rms <= 1e-12:
        raise ValueError("audio must contain measurable non-silent energy")
    scale = TARGET_RMS / rms
    return (samples * scale).astype(np.float32, copy=False)


def extract_mfcc78(audio: np.ndarray, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Extract a deterministic 78D MFCC/chroma/spectral-contrast fingerprint.

    This is a model-free *timbral retrieval benchmark* representation, not a
    genre classifier and not a replacement for CLaMP/MERT semantic embeddings.
    Input RMS is normalized before extraction so a pure gain change does not
    alter the intended timbral representation.
    """

    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim != 1:
        raise ValueError("MFCC baseline requires mono audio")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if samples.size < N_FFT:
        raise ValueError(f"audio is too short for MFCC baseline: need >= {N_FFT} samples")
    if not np.all(np.isfinite(samples)):
        raise ValueError("audio must contain only finite samples")

    samples = _normalize_analysis_level(samples)

    mfcc = librosa.feature.mfcc(
        y=samples,
        sr=sample_rate,
        n_mfcc=N_MFCC,
        dct_type=2,
        norm="ortho",
        lifter=0,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        power=2.0,
    )
    chroma = librosa.feature.chroma_stft(
        y=samples,
        sr=sample_rate,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_chroma=N_CHROMA,
    )
    contrast = librosa.feature.spectral_contrast(
        y=samples,
        sr=sample_rate,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_bands=N_CONTRAST_BANDS,
        fmin=200.0,
        quantile=0.02,
        linear=False,
    )

    vector = np.concatenate(
        (
            mfcc.mean(axis=1),
            mfcc.std(axis=1),
            chroma.mean(axis=1),
            chroma.std(axis=1),
            contrast.mean(axis=1),
            contrast.std(axis=1),
        )
    ).astype(np.float32, copy=False)

    if vector.shape != (EMBEDDING_DIM,):
        raise RuntimeError(f"unexpected MFCC baseline dimension: {vector.shape}")
    if not np.all(np.isfinite(vector)):
        raise ValueError("MFCC baseline produced non-finite values")

    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError("MFCC baseline produced a zero-norm vector")
    return (vector / norm).astype(np.float32, copy=False)


def _slice_interval(
    audio: np.ndarray,
    *,
    sample_rate: int,
    start_s: float | None,
    end_s: float | None,
) -> tuple[np.ndarray, str]:
    if (start_s is None) != (end_s is None):
        raise ValueError("start_s and end_s must be provided together")
    if start_s is None and end_s is None:
        return audio, "full"

    assert start_s is not None
    assert end_s is not None
    duration_s = audio.size / float(sample_rate)
    if start_s < 0 or end_s <= start_s:
        raise ValueError("segment bounds must satisfy 0 <= start_s < end_s")
    if end_s > duration_s:
        raise ValueError(
            f"segment end exceeds audio duration: end_s={end_s:.6f}, duration={duration_s:.6f}"
        )

    start = int(round(start_s * sample_rate))
    end = int(round(end_s * sample_rate))
    segment = audio[start:end]
    if segment.size < N_FFT:
        raise ValueError(f"segment is too short for MFCC baseline: need >= {N_FFT} samples")
    return segment, "segment"


class MFCCBaselineExtractor:
    """Audio-only benchmark extractor using the shared retrieval identity contract."""

    @property
    def info(self) -> RetrievalBackendInfo:
        return mfcc_baseline_info()

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        if not track_id.strip():
            raise ValueError("track_id must not be empty")

        audio, sample_rate = load_audio(path, sample_rate=SAMPLE_RATE)
        selected, scope = _slice_interval(
            audio,
            sample_rate=sample_rate,
            start_s=start_s,
            end_s=end_s,
        )
        values = extract_mfcc78(selected, sample_rate=sample_rate)

        if scope == "full":
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="full",
                track_id=track_id,
            )
        else:
            assert start_s is not None
            assert end_s is not None
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="segment",
                track_id=track_id,
                start_s=start_s,
                end_s=end_s,
            )

        return EmbeddingVector.normalized(
            identity,
            values.tolist(),
            expected_dim=EMBEDDING_DIM,
        )
