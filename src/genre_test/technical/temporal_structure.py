"""Deterministic temporal-structure measurements for research and repair evidence.

The metrics in this module are objective signal descriptors. They are not an
AI-origin classifier and must not be surfaced as AI/HUMAN/SUNO probabilities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import librosa
import numpy as np
from scipy.signal import find_peaks, medfilt

ALGORITHM_ID = "genre-test-temporal-structure/1"


@dataclass(frozen=True)
class TemporalStructureConfig:
    n_fft: int = 2048
    hop_length: int = 512
    n_mels: int = 40
    n_mfcc: int = 13
    grid_subdivisions_per_beat: int = 4
    beat_lock_tolerance_ms: float = 20.0
    transient_window_ms: float = 80.0
    transient_preroll_ms: float = 30.0
    max_transients: int = 64
    spectral_min_hz: float = 1000.0
    spectral_peak_prominence_db: float = 4.0


@dataclass(frozen=True)
class TemporalStructureProfileV1:
    schema: str
    algorithm_identity: str
    sample_rate_hz: int
    duration_s: float
    status: str
    mfcc: dict[str, float | None]
    rhythm: dict[str, float | int | None]
    transients: dict[str, float | int | None]
    spectral_artifacts: dict[str, float | int | None]
    configuration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finite(value: float | np.floating[Any] | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if np.isfinite(value) else None


def _cv(values: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return None
    mean = float(np.mean(values))
    if abs(mean) <= 1e-12:
        return 0.0 if np.allclose(values, 0.0) else None
    return float(np.std(values) / abs(mean))


def _to_mono(audio: np.ndarray) -> np.ndarray:
    y = np.asarray(audio, dtype=np.float32)
    if y.ndim == 1:
        mono = y
    elif y.ndim == 2:
        if y.shape[0] <= 8 and y.shape[0] < y.shape[1]:
            mono = np.mean(y, axis=0, dtype=np.float32)
        else:
            mono = np.mean(y, axis=1, dtype=np.float32)
    else:
        raise ValueError("audio must be mono or 2-D multichannel PCM")
    if mono.size == 0:
        raise ValueError("audio must not be empty")
    if not np.all(np.isfinite(mono)):
        raise ValueError("audio contains NaN or infinite samples")
    return np.ascontiguousarray(mono, dtype=np.float32)


def _mfcc_metrics(y: np.ndarray, sr: int, cfg: TemporalStructureConfig) -> dict[str, float | None]:
    n_fft = min(cfg.n_fft, max(256, 2 ** int(np.floor(np.log2(max(256, y.size))))))
    hop = min(cfg.hop_length, max(64, n_fft // 4))
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop,
        n_mels=cfg.n_mels,
        power=2.0,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    mfcc = librosa.feature.mfcc(S=log_mel, n_mfcc=cfg.n_mfcc)
    if mfcc.shape[1] < 2:
        return {
            "mfcc_delta_variance": None,
            "mfcc_delta2_variance": None,
            "mfcc_trajectory_path_length": None,
            "mfcc_trajectory_acceleration_p95": None,
        }
    delta = librosa.feature.delta(mfcc, order=1, mode="nearest")
    delta2 = librosa.feature.delta(mfcc, order=2, mode="nearest")
    step = np.linalg.norm(np.diff(mfcc, axis=1), axis=0)
    accel = np.linalg.norm(delta2, axis=0)
    return {
        "mfcc_delta_variance": _finite(np.mean(np.var(delta, axis=1))),
        "mfcc_delta2_variance": _finite(np.mean(np.var(delta2, axis=1))),
        "mfcc_trajectory_path_length": _finite(np.mean(step)),
        "mfcc_trajectory_acceleration_p95": _finite(np.percentile(accel, 95)),
    }


def _rhythm_metrics(
    y: np.ndarray, sr: int, cfg: TemporalStructureConfig
) -> tuple[dict[str, float | int | None], np.ndarray, np.ndarray, np.ndarray]:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=cfg.hop_length)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=cfg.hop_length,
        units="frames",
        backtrack=False,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=cfg.hop_length)

    ioi_cv = _cv(np.diff(onset_times)) if onset_times.size >= 2 else None
    tempo_value: float | None = None
    beat_frames = np.asarray([], dtype=int)
    if onset_env.size:
        tempo, beat_frames = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=cfg.hop_length,
            trim=False,
        )
        tempo_array = np.asarray(tempo, dtype=np.float64).reshape(-1)
        if tempo_array.size and np.isfinite(tempo_array[0]) and tempo_array[0] > 0:
            tempo_value = float(tempo_array[0])

    deviations_ms = np.asarray([], dtype=np.float64)
    if tempo_value is not None and onset_times.size and beat_frames.size:
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=cfg.hop_length)
        if beat_times.size:
            subdivision_s = 60.0 / tempo_value / cfg.grid_subdivisions_per_beat
            phase = (onset_times - float(beat_times[0])) / subdivision_s
            deviations_ms = np.abs(phase - np.round(phase)) * subdivision_s * 1000.0

    if deviations_ms.size:
        grid_median = _finite(np.median(deviations_ms))
        grid_iqr = _finite(np.percentile(deviations_ms, 75) - np.percentile(deviations_ms, 25))
        locked_ratio = _finite(np.mean(deviations_ms <= cfg.beat_lock_tolerance_ms))
    else:
        grid_median = grid_iqr = locked_ratio = None

    return (
        {
            "onset_count": int(onset_times.size),
            "tempo_bpm": _finite(tempo_value),
            "onset_grid_deviation_ms_median": grid_median,
            "onset_grid_deviation_ms_iqr": grid_iqr,
            "inter_onset_interval_cv": _finite(ioi_cv),
            "beat_locked_onset_ratio": locked_ratio,
        },
        onset_frames,
        onset_times,
        onset_env,
    )


def _attack_logmel_vector(segment: np.ndarray, sr: int) -> np.ndarray:
    if segment.size < 32:
        return np.zeros(24, dtype=np.float64)
    n_fft = min(512, max(64, 2 ** int(np.floor(np.log2(segment.size)))))
    mel = librosa.feature.melspectrogram(
        y=segment,
        sr=sr,
        n_fft=n_fft,
        hop_length=max(16, n_fft // 4),
        n_mels=24,
        power=2.0,
    )
    vector = np.log1p(np.mean(mel, axis=1, dtype=np.float64))
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 1e-12 else np.zeros_like(vector)


def _transient_metrics(
    y: np.ndarray,
    sr: int,
    onset_frames: np.ndarray,
    onset_times: np.ndarray,
    onset_env: np.ndarray,
    cfg: TemporalStructureConfig,
) -> dict[str, float | int | None]:
    if onset_times.size == 0:
        return {
            "transient_count": 0,
            "attack_similarity_median": None,
            "attack_similarity_p95": None,
            "attack_energy_cv": None,
            "attack_time_cv": None,
            "spectral_flux_cv": None,
        }

    count = min(int(onset_times.size), cfg.max_transients)
    window_samples = max(32, int(round(sr * cfg.transient_window_ms / 1000.0)))
    preroll = int(round(sr * cfg.transient_preroll_ms / 1000.0))
    vectors: list[np.ndarray] = []
    energies: list[float] = []
    peak_times_ms: list[float] = []

    for onset_s in onset_times[:count]:
        onset_sample = int(round(float(onset_s) * sr))
        start = max(0, onset_sample - preroll)
        segment = y[start : min(y.size, start + window_samples)]
        if segment.size < 16:
            continue
        vectors.append(_attack_logmel_vector(segment, sr))
        energies.append(float(np.sqrt(np.mean(np.square(segment, dtype=np.float64)))))
        peak_index = int(np.argmax(np.abs(segment)))
        peak_times_ms.append(peak_index / sr * 1000.0)

    similarities = np.asarray([], dtype=np.float64)
    if len(vectors) >= 2:
        matrix = np.stack(vectors, axis=0)
        similarity_matrix = matrix @ matrix.T
        upper = np.triu_indices(similarity_matrix.shape[0], k=1)
        similarities = similarity_matrix[upper]

    flux_values = onset_env[onset_frames] if onset_frames.size else np.asarray([], dtype=np.float64)
    return {
        "transient_count": int(len(vectors)),
        "attack_similarity_median": _finite(np.median(similarities)) if similarities.size else None,
        "attack_similarity_p95": _finite(np.percentile(similarities, 95)) if similarities.size else None,
        "attack_energy_cv": _finite(_cv(np.asarray(energies))),
        "attack_time_cv": _finite(_cv(np.asarray(peak_times_ms))),
        "spectral_flux_cv": _finite(_cv(np.asarray(flux_values))),
    }


def _spectral_artifact_metrics(
    y: np.ndarray, sr: int, cfg: TemporalStructureConfig
) -> dict[str, float | int | None]:
    n_fft = min(4096, max(512, 2 ** int(np.floor(np.log2(max(512, min(y.size, 4096)))))))
    hop = max(128, n_fft // 4)
    magnitude = np.abs(librosa.stft(y=y, n_fft=n_fft, hop_length=hop))
    if magnitude.shape[1] == 0:
        return {
            "periodic_peak_score": None,
            "peak_spacing_hz": None,
            "peak_persistence": None,
            "candidate_peak_count": 0,
        }
    mean_db = librosa.amplitude_to_db(np.mean(magnitude, axis=1), ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mask = freqs >= cfg.spectral_min_hz
    if np.count_nonzero(mask) < 9:
        return {
            "periodic_peak_score": None,
            "peak_spacing_hz": None,
            "peak_persistence": None,
            "candidate_peak_count": 0,
        }
    high_db = mean_db[mask]
    high_freqs = freqs[mask]
    baseline = medfilt(high_db, kernel_size=9)
    residual = high_db - baseline
    peaks, properties = find_peaks(residual, prominence=cfg.spectral_peak_prominence_db)
    if peaks.size < 2:
        return {
            "periodic_peak_score": 0.0,
            "peak_spacing_hz": None,
            "peak_persistence": None,
            "candidate_peak_count": int(peaks.size),
        }

    order = np.argsort(properties["prominences"])[::-1][: min(24, peaks.size)]
    selected = np.sort(peaks[order])
    selected_freqs = high_freqs[selected]
    spacings = np.diff(selected_freqs)
    spacing_mean = float(np.mean(spacings)) if spacings.size else 0.0
    spacing_cv = float(np.std(spacings) / spacing_mean) if spacing_mean > 1e-12 else 1.0
    regularity = float(np.clip(1.0 - spacing_cv, 0.0, 1.0))

    high_mag = magnitude[mask]
    frame_db = librosa.amplitude_to_db(high_mag, ref=np.max)
    persistence_values: list[float] = []
    for peak in selected:
        lo = max(0, int(peak) - 4)
        hi = min(frame_db.shape[0], int(peak) + 5)
        neighborhood = frame_db[lo:hi]
        local_baseline = np.median(neighborhood, axis=0)
        persistence_values.append(float(np.mean(frame_db[int(peak)] - local_baseline >= 3.0)))

    return {
        "periodic_peak_score": _finite(regularity),
        "peak_spacing_hz": _finite(np.median(spacings)) if spacings.size else None,
        "peak_persistence": _finite(np.mean(persistence_values)) if persistence_values else None,
        "candidate_peak_count": int(peaks.size),
    }


def analyze_temporal_structure(
    audio: np.ndarray,
    sample_rate_hz: int,
    *,
    config: TemporalStructureConfig | None = None,
) -> TemporalStructureProfileV1:
    """Measure temporal/spectral structure without making provenance claims."""

    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    cfg = config or TemporalStructureConfig()
    if cfg.grid_subdivisions_per_beat <= 0:
        raise ValueError("grid_subdivisions_per_beat must be positive")
    if cfg.max_transients <= 0:
        raise ValueError("max_transients must be positive")

    y = _to_mono(audio)
    duration_s = float(y.size / sample_rate_hz)
    mfcc = _mfcc_metrics(y, sample_rate_hz, cfg)
    rhythm, onset_frames, onset_times, onset_env = _rhythm_metrics(y, sample_rate_hz, cfg)
    transients = _transient_metrics(y, sample_rate_hz, onset_frames, onset_times, onset_env, cfg)
    spectral = _spectral_artifact_metrics(y, sample_rate_hz, cfg)
    return TemporalStructureProfileV1(
        schema="temporal-structure-profile/1",
        algorithm_identity=ALGORITHM_ID,
        sample_rate_hz=int(sample_rate_hz),
        duration_s=duration_s,
        status="OK",
        mfcc=mfcc,
        rhythm=rhythm,
        transients=transients,
        spectral_artifacts=spectral,
        configuration=asdict(cfg),
    )
