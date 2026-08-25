from genre_test.themed_gui import (
    DARK_LABEL,
    DEFAULT_THEME,
    LIGHT_LABEL,
    PALETTES,
    THEME_LABELS,
    normalize_theme_label,
)


def test_dark_theme_is_default():
    assert DEFAULT_THEME == DARK_LABEL
    assert THEME_LABELS == (DARK_LABEL, LIGHT_LABEL)


def test_theme_palettes_exist_for_both_modes():
    assert set(PALETTES) == {DARK_LABEL, LIGHT_LABEL}
    assert PALETTES[DARK_LABEL].window != PALETTES[LIGHT_LABEL].window
    assert PALETTES[DARK_LABEL].field != PALETTES[LIGHT_LABEL].field


def test_unknown_theme_falls_back_to_dark():
    assert normalize_theme_label("unknown") == DARK_LABEL
