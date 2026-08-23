import pytest

from genre_test.aggregate import aggregate_predictions, broad_genre


def test_broad_genre_discogs_label():
    assert broad_genre("Electronic---House") == "Electronic"


def test_aggregate_predictions_mean_across_windows():
    windows = [
        [
            {"label": "Electronic---House", "score": 0.8},
            {"label": "Rock---Alternative Rock", "score": 0.2},
        ],
        [
            {"label": "Electronic---House", "score": 0.6},
            {"label": "Rock---Alternative Rock", "score": 0.4},
        ],
    ]
    styles, genres = aggregate_predictions(windows, top_k=5)
    assert styles[0].label == "Electronic---House"
    assert styles[0].score == pytest.approx(0.7)
    assert genres[0].label == "Electronic"
    assert genres[0].score == pytest.approx(0.7)
