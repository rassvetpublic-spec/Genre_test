import numpy as np

from genre_test.audio import iter_audio_files, select_windows


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


def test_service_directories_are_ignored_by_default(tmp_path):
    normal = tmp_path / "song.mp3"
    normal.write_bytes(b"audio")
    service = tmp_path / "Resources" / "audioAlg" / "cache.mp3"
    service.parent.mkdir(parents=True)
    service.write_bytes(b"cache")
    results = tmp_path / "results" / "old.wav"
    results.parent.mkdir(parents=True)
    results.write_bytes(b"old")

    assert iter_audio_files(tmp_path) == [normal]
    assert set(iter_audio_files(tmp_path, include_service_dirs=True)) == {
        normal,
        service,
        results,
    }


def test_explicit_file_inside_service_directory_is_still_allowed(tmp_path):
    service = tmp_path / "Resources" / "audioAlg" / "cache.mp3"
    service.parent.mkdir(parents=True)
    service.write_bytes(b"cache")
    assert iter_audio_files(service) == [service]
