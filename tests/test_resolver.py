from genre_test.models import StyleScore
from genre_test.resolver import resolve_genre


def test_hybrid_uses_best_style_across_two_close_families():
    styles = [
        StyleScore("Rock---Pop Rock", 0.216),
        StyleScore("Pop---Ballad", 0.120),
        StyleScore("Pop---Europop", 0.099),
    ]
    broad = [StyleScore("Pop", 0.363), StyleScore("Rock", 0.346)]
    r = resolve_genre(styles, broad)
    assert r.classification == "hybrid"
    assert r.resolved_genre == "Pop Rock"
    assert r.confidence == "low-medium"


def test_clear_family_is_high_confidence():
    styles = [StyleScore("Rock---Alternative Rock", 0.172)]
    broad = [StyleScore("Rock", 0.717), StyleScore("Electronic", 0.147)]
    r = resolve_genre(styles, broad)
    assert r.classification == "primary"
    assert r.resolved_genre == "Alternative Rock"
    assert r.confidence == "high"
