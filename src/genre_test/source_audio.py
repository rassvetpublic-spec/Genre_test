from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

_PCM_BITS = {
    "PCM_U8": 8,
    "PCM_S8": 8,
    "PCM_16": 16,
    "PCM_24": 24,
    "PCM_32": 32,
    "FLOAT": 32,
    "DOUBLE": 64,
}


@dataclass(frozen=True)
class SourceAudioInfo:
    format: str
    subtype: str
    sample_rate: int
    channels: int
    duration_s: float
    bit_depth: int | None
    bitrate_kbps: float | None

    @property
    def channel_label(self) -> str:
        if self.channels == 1:
            return "mono"
        if self.channels == 2:
            return "stereo"
        return f"{self.channels} ch"


def probe_source_audio(path: str | Path) -> SourceAudioInfo | None:
    """Read container/PCM properties without confusing them with analysis resampling."""
    source = Path(path)
    try:
        info = sf.info(str(source))
    except Exception:
        return None

    duration_s = float(info.frames / info.samplerate) if info.samplerate else 0.0
    bit_depth = _PCM_BITS.get(info.subtype)
    bitrate_kbps: float | None = None
    if bit_depth and info.samplerate and info.channels:
        bitrate_kbps = info.samplerate * info.channels * bit_depth / 1000.0
    elif duration_s > 0.0:
        try:
            bitrate_kbps = source.stat().st_size * 8.0 / duration_s / 1000.0
        except OSError:
            pass

    return SourceAudioInfo(
        format=info.format or source.suffix.lstrip(".").upper() or "unknown",
        subtype=info.subtype or "unknown",
        sample_rate=int(info.samplerate),
        channels=int(info.channels),
        duration_s=duration_s,
        bit_depth=bit_depth,
        bitrate_kbps=bitrate_kbps,
    )


def format_source_audio(path: str | Path) -> str | None:
    info = probe_source_audio(path)
    if info is None:
        return None
    sample_rate_khz = info.sample_rate / 1000.0
    parts = [f"{info.format} {info.subtype}", f"{sample_rate_khz:g} kHz"]
    if info.bit_depth:
        parts.append(f"{info.bit_depth}-bit")
    parts.append(info.channel_label)
    if info.bitrate_kbps is not None:
        parts.append(f"{info.bitrate_kbps:.0f} kbps")
    return " | ".join(parts)
