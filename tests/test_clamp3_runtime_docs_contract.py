from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_clamp3_runtime_p0_uses_root_launcher() -> None:
    text = (ROOT / "docs" / "CLAMP3_RUNTIME_P0.md").read_text(encoding="utf-8")

    assert ".\\Genre_test_START.cmd retrieval-setup" in text
    assert "pwsh -File .\\scripts\\setup_clamp3_runtime.ps1" not in text


def test_clamp3_roadmap_uses_supported_core_python_baseline() -> None:
    text = (ROOT / "docs" / "CLAMP3_ROADMAP.md").read_text(encoding="utf-8")

    assert "Python 3.13 primary/default" in text
    assert "Python 3.12 supported fallback" in text
    assert "Python 3.11 / 3.12 / 3.13" not in text
