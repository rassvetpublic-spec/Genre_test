from __future__ import annotations

import librosa
import numpy as np

from .analysis_policy import INSUFFICIENT_AUDIO_SECONDS
from .models import AudioFeatures

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# Krumhansl-Schmuckler key profiles.
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

TEMPO_HOP_LENGTH = 256
SHORT_LOOP_MAX_SECONDS = 30.0
SHORT_LOOP_BEAT_COUNTS = (8, 16, 32, 64, 128)
METRIC_TEMPO_RATIOS = (0.5, 2.0 / 3.0, 1.0, 1.5, 2.0)
TEMPO_MIN_BPM = 45.0
TEMPO_MAX_BPM = 240.0


def _estimate_key(chroma: np.ndarray) -> tuple[str | None, str | None]:
    if chroma.size == 0:
        return None, None
    profile = np.nan_to_num(np.mean(chroma, axis=1), nan=0.0)
    if not np.any(profile):
        return None, None

    scores: list[tuple[float, str, str]] = []
    for tonic in range(12):
        major = np.roll(MAJOR_PROFILE, tonic)
        minor = np.roll(MINOR_PROFILE, tonic)
        scores.append((float(np.corrcoef(profile, major)[0, 1]), PITCH_CLASSES[tonic], "major"))
        scores.append((float(np.corrcoef(profile, minor)[0, 1]), PITCH_CLASSES[tonic], "minor"))
    score, key, mode = max(scores, key=lambda x: -np.inf if np.isnan(x[0]) else x[0])
    if np.isnan(score):
        return None, None
    return key, mode


def _resolve_short_loop_tempo(base_bpm: float, duration_s: float) -> float:
    """Resolve half/double/3:2 metric ambiguity when a short loop has strong grid evidence."""
    if base_bpm <= 0.0 or duration_s <= 0.0 or duration_s > SHORT_LOOP_MAX_SECONDS:
        return base_bpm

    candidates: list[tuple[float, float, float, float, int]] = []
    for ratio in METRIC_TEMPO_RATIOS:
        candidate = base_bpm * ratio
        if not TEMPO_MIN_BPM <= candidate <= TEMPO_MAX_BPM:
            continue
        beat_count = duration_s * candidate / 60.0
        expected = min(SHORT_LOOP_BEAT_COUNTS, key=lambda value: abs(beat_count - value))
        error = abs(beat_count - expected)
        relative_error = error / expected
        candidates.append((relative_error, error, abs(ratio - 1.0), candidate, expected))

    if not candidates:
        return base_bpm

    relative_error, error, _, _, expected = min(candidates)
    if error > 0.25 or relative_error > 0.005:
        return base_bpm

    snapped = expected * 60.0 / duration_s
    if TEMPO_MIN_BPM <= snapped <= TEMPO_MAX_BPM:
        return snapped
    return base_bpm


def _estimate_tempo(audio: np.ndarray, sr: int, duration_s: float) -> float | None:
    onset = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=TEMPO_HOP_LENGTH)
    if onset.size == 0 or not np.any(onset > 0.0):
        return None
    tempo, _ = librosa.beat.beat_track(
        onset_envelope=onset,
        sr=sr,
        hop_length=TEMPO_HOP_LENGTH,
    )
    if not np.size(tempo):
        return None
    base_bpm = float(np.asarray(tempo).reshape(-1)[0])
    if not np.isfinite(base_bpm) or base_bpm <= 0.0:
        return None
    return _resolve_short_loop_tempo(base_bpm, duration_s)


def extract_lightweight_audio_features(audio: np.ndarray, sr: int) -> AudioFeatures:
    """Extract warning-free basic features when audio is too short for genre inference."""
    duration = float(audio.size / sr) if sr else 0.0
    if audio.size == 0:
        return AudioFeatures(
            duration_s=round(duration, 3),
            sample_rate=sr,
            bpm=None,
            key=None,
            mode=None,
            rms=0.0,
            spectral_centroid_hz=0.0,
            spectral_rolloff_hz=0.0,
            zero_crossing_rate=0.0,
        )

    samples = np.asarray(audio, dtype=np.float64)
    # Silence has exact zero values for every lightweight metric. Returning it
    # directly avoids unnecessary FFT/backend initialization and keeps the
    # short-audio path warning-free across supported Python/Numpy versions.
    if not np.any(samples):
        return AudioFeatures(
            duration_s=round(duration, 3),
            sample_rate=sr,
            bpm=None,
            key=None,
            mode=None,
            rms=0.0,
            spectral_centroid_hz=0.0,
            spectral_rolloff_hz=0.0,
            zero_crossing_rate=0.0,
        )

    rms = float(np.sqrt(np.mean(np.square(samples))))
    if samples.size > 1:
        zcr = float(np.mean(np.signbit(samples[1:]) != np.signbit(samples[:-1])))
    else:
        zcr = 0.0

    magnitude = np.abs(np.fft.rfft(samples))
    total = float(np.sum(magnitude))
    if total > 0.0:
        frequencies = np.fft.rfftfreq(samples.size, d=1.0 / sr)
        centroid = float(np.sum(frequencies * magnitude) / total)
        cumulative = np.cumsum(magnitude)
        index = int(np.searchsorted(cumulative, total * 0.85, side="left"))
        index = min(index, frequencies.size - 1)
        rolloff = float(frequencies[index])
    else:
        centroid = 0.0
        rolloff = 0.0

    return AudioFeatures(
        duration_s=round(duration, 3),
        sample_rate=sr,
        bpm=None,
        key=None,
        mode=None,
        rms=round(rms, 6),
        spectral_centroid_hz=round(centroid, 2),
        spectral_rolloff_hz=round(rolloff, 2),
        zero_crossing_rate=round(zcr, 6),
    )


def extract_audio_features(audio: np.ndarray, sr: int) -> AudioFeatures:
    duration = float(audio.size / sr)
    if duration < INSUFFICIENT_AUDIO_SECONDS:
        return extract_lightweight_audio_features(audio, sr)

    bpm = _estimate_tempo(audio, sr, duration)

    chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
    key, mode = _estimate_key(chroma)

    rms = float(np.mean(librosa.feature.rms(y=audio)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr, roll_percent=0.85)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio)))

    return AudioFeatures(
        duration_s=round(duration, 3),
        sample_rate=sr,
        bpm=round(bpm, 2) if bpm is not None else None,
        key=key,
        mode=mode,
        rms=round(rms, 6),
        spectral_centroid_hz=round(centroid, 2),
        spectral_rolloff_hz=round(rolloff, 2),
        zero_crossing_rate=round(zcr, 6),
    )
