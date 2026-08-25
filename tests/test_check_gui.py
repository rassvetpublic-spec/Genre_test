from genre_test.check_gui import (
    CHECK_DESCRIPTION,
    CHECK_MODE_DESCRIPTION,
    VERSION_MODE_LABELS,
)
from genre_test.runtime_health_gui import (
    EXPERT_CONTROLS_DESCRIPTION,
    VALIDATION_DESCRIPTION,
    VALIDATION_MODE_DESCRIPTION,
)


def test_validation_and_check_have_distinct_user_descriptions() -> None:
    assert "повторно анализирует" in VALIDATION_DESCRIPTION
    assert "Аудио повторно не анализируется" in CHECK_DESCRIPTION
    assert VALIDATION_DESCRIPTION != CHECK_DESCRIPTION


def test_mode_descriptions_cover_expected_modes() -> None:
    assert "Быстрый" in VALIDATION_MODE_DESCRIPTION
    assert "Точный" in VALIDATION_MODE_DESCRIPTION
    assert "Auto/Fast/Accurate/Expert" in CHECK_MODE_DESCRIPTION
    assert VERSION_MODE_LABELS["Expert"] == "expert"


def test_expert_controls_explain_windows_and_top_k() -> None:
    assert "окна MAEST" in EXPERT_CONTROLS_DESCRIPTION
    assert "жанровые кандидаты" in EXPERT_CONTROLS_DESCRIPTION
