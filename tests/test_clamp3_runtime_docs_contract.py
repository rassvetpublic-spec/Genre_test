from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_clamp3_runtime_p0_uses_root_launcher() -> None:
    text = (ROOT / "docs" / "CLAMP3_RUNTIME_P0.md").read_text(encoding="utf-8")

    assert ".\\Genre_test_START.cmd retrieval-setup" in text
    assert "pwsh -File .\\scripts\\setup_clamp3_runtime.ps1" not in text
