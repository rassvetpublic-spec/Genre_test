from __future__ import annotations

import numpy as np
import soundfile as sf

from genre_test.source_audio import format_source_audio, probe_source_audio


def test_pcm16_stereo_bitrate_is_native_source_rate(tmp_path) -> None:
    path = tmp_path / "source.wav"
    sf.write(path, np.zeros((4410, 2), dtype=np.float32), 44100, subtype="PCM_16")

    info = probe_source_audio(path)

    assert info is not None
    assert info.sample_rate == 44100
    assert info.channels == 2
    assert info.bit_depth == 16
    assert info.bitrate_kbps == 1411.2
    assert "44.1 kHz" in (format_source_audio(path) or "")
    assert "1411 kbps" in (format_source_audio(path) or "")


def test_pcm24_48k_stereo_bitrate(tmp_path) -> None:
    path = tmp_path / "master.wav"
    sf.write(path, np.zeros((4800, 2), dtype=np.float32), 48000, subtype="PCM_24")

    info = probe_source_audio(path)

    assert info is not None
    assert info.sample_rate == 48000
    assert info.channels == 2
    assert info.bit_depth == 24
    assert info.bitrate_kbps == 2304.0
    assert "48 kHz" in (format_source_audio(path) or "")
    assert "2304 kbps" in (format_source_audio(path) or "")
