from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v04_release_bootstrap_runtime_contract() -> None:
    script = (ROOT / "scripts" / "release_bootstrap.ps1").read_text(encoding="utf-8")

    assert "Windows PowerShell 5.1 compatible" in script
    assert "Python 3.11/3.12/3.13 x64" in script
    assert "foreach ($selector in @('-3.13', '-3.12', '-3.11'))" in script
    assert "Python.Python.3.12" in script
    assert "$torchVersion = '2.12.1'" in script
    assert "whl/cu130" in script
    assert "whl/cpu" in script
    assert "Test-NvidiaHardware" in script
    assert "Win32_VideoController" in script
    assert "VEN_10DE" in script
    assert "torch.cuda.get_arch_list()" in script
    assert "blackwell = major in {10, 11, 12}" in script
    assert "Compatible PyTorch already present" in script
    assert "genre-test doctor failed" in script
    assert "genre-test-gui.exe" in script


def test_packaged_launcher_prefers_release_bootstrap() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'scripts\\release_bootstrap.ps1' in launcher
    assert 'if defined RELEASE_BOOTSTRAP goto RELEASE_PREFLIGHT' in launcher


def test_portable_docs_are_v04_and_not_fixed_to_old_path() -> None:
    english = (ROOT / "PORTABLE_README.txt").read_text(encoding="utf-8")
    russian = (ROOT / "README_RU.txt").read_text(encoding="utf-8")

    assert "Genre_test 0.4.0" in english
    assert "Python 3.11, 3.12 or 3.13 x64" in english
    assert "CUDA 13.0 / cu130" in english
    assert "no fixed install path is required" in english
    assert "Genre_test 0.4.0" in russian
    assert "Python 3.11 / 3.12 / 3.13 x64" in russian
    assert "CUDA 13.0 / cu130" in russian
    assert "Фиксированный путь больше НЕ обязателен" in russian
