from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}


def load_audio(path: Path, sample_rate: int) -> tuple[np.ndarray, int]:
    audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0:
        raise ValueError(f"Empty audio: {path}")
    peak = float(np.max(np.abs(audio)))
    if peak > 1.0:
        audio = audio / peak
    return audio, sr


def select_windows(
    audio: np.ndarray,
    sr: int,
    window_seconds: float = 30.0,
    count: int = 5,
) -> list[np.ndarray]:
    if count < 1:
        raise ValueError("count must be >= 1")
    width = max(1, round(window_seconds * sr))
    n = audio.size

    if n <= width:
        padded = np.pad(audio, (0, width - n))
        return [padded.astype(np.float32, copy=False)]

    max_start = n - width
    starts = np.linspace(0, max_start, num=min(count, max_start + 1), dtype=np.int64)
    # Preserve order and eliminate accidental duplicates on very short clips.
    starts = np.unique(starts)
    return [audio[int(s) : int(s) + width].astype(np.float32, copy=False) for s in starts]


def iter_audio_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported audio extension: {path.suffix}")
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(path)
    return sorted(
        p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
