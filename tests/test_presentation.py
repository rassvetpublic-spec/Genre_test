from genre_test.presentation import tempo_candidates


def test_tempo_candidates():
    value = tempo_candidates(81.52)
    assert "81.52 BPM" in value
    assert "40.76" in value
    assert "163.04" in value
