import numpy as np

from genre_test.audio import select_windows


def test_short_audio_is_padded_to_one_window():
    audio = np.ones(100, dtype=np.float32)
    windows = select_windows(audio, sr=10, window_seconds=30.0, count=5)
    assert len(windows) == 1
    assert len(windows[0]) == 300
    assert np.allclose(windows[0][:100], 1.0)
    assert np.allclose(windows[0][100:], 0.0)


def test_long_audio_uses_requested_number_of_windows():
    audio = np.arange(1000, dtype=np.float32)
    windows = select_windows(audio, sr=10, window_seconds=10.0, count=5)
    assert len(windows) == 5
    assert all(len(w) == 100 for w in windows)
