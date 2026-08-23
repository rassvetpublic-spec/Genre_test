from genre_test.track_identity import identify_track


def test_track_identity_is_content_based(tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "moved.mp3"
    a.write_bytes(b"same audio bytes")
    b.write_bytes(b"same audio bytes")
    assert identify_track(a).track_id == identify_track(b).track_id


def test_track_identity_changes_with_content(tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    assert identify_track(a).track_id != identify_track(b).track_id
