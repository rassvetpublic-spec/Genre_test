import pytest

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
    assert r.secondary_style == "Pop Ballad"
    assert r.confidence == "low-medium"
    assert r.family_ratio == pytest.approx(0.953168, abs=1e-6)


def test_clear_family_and_clear_style_are_high_confidence():
    styles = [
        StyleScore("Rock---Heavy Metal", 0.266),
        StyleScore("Rock---Hard Rock", 0.120),
        StyleScore("Pop---Europop", 0.029),
    ]
    broad = [StyleScore("Rock", 0.814), StyleScore("Pop", 0.060)]
    r = resolve_genre(styles, broad)
    assert r.classification == "primary"
    assert r.resolved_genre == "Heavy Metal"
    assert r.secondary_style == "Hard Rock"
    assert r.confidence == "high"
    assert r.style_margin == pytest.approx(0.548872, abs=1e-6)


def test_clear_family_but_close_fine_styles_reduce_confidence():
    styles = [
        StyleScore("Rock---Alternative Rock", 0.1724),
        StyleScore("Rock---Pop Punk", 0.1480),
        StyleScore("Electronic---Drum n Bass", 0.0489),
    ]
    broad = [StyleScore("Rock", 0.7173), StyleScore("Electronic", 0.1475)]
    r = resolve_genre(styles, broad)
    assert r.classification == "primary"
    assert r.resolved_genre == "Alternative Rock"
    assert r.confidence == "medium"
    assert r.style_margin == pytest.approx(0.141531, abs=1e-6)


def test_stronger_style_in_secondary_family_is_exposed_as_conflict():
    styles = [
        StyleScore("Pop---Schlager", 0.1263),
        StyleScore("Rock---Power Metal", 0.1029),
        StyleScore("Rock---Heavy Metal", 0.0978),
    ]
    broad = [StyleScore("Rock", 0.5027), StyleScore("Pop", 0.3781)]
    r = resolve_genre(styles, broad)
    assert r.classification == "primary"
    assert r.resolved_genre == "Power Metal"
    assert r.secondary_style == "Schlager"
    assert r.confidence == "low-medium"
    assert r.style_margin is not None and r.style_margin < 0


def test_generic_vocal_label_gets_family_context():
    styles = [
        StyleScore("Pop---Vocal", 0.1624),
        StyleScore("Electronic---Dance-pop", 0.1465),
        StyleScore("Pop---Ballad", 0.0948),
    ]
    broad = [StyleScore("Pop", 0.4281), StyleScore("Electronic", 0.3066)]
    r = resolve_genre(styles, broad)
    assert r.resolved_genre == "Vocal Pop"
    assert r.secondary_style == "Dance-pop"
    assert r.confidence == "low-medium"


def test_family_ratio_can_trigger_hybrid_when_absolute_margin_does_not():
    styles = [
        StyleScore("Electronic---Dance-pop", 0.30),
        StyleScore("Pop---Indie Pop", 0.18),
    ]
    broad = [StyleScore("Electronic", 0.50), StyleScore("Pop", 0.41)]
    r = resolve_genre(styles, broad)
    assert r.family_margin == pytest.approx(0.09)
    assert r.family_ratio == pytest.approx(0.82)
    assert r.classification == "hybrid"
    assert r.confidence == "low-medium"
