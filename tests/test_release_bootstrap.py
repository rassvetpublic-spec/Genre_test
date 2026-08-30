from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_bootstrap_runtime_contract() -> None:
    script = (ROOT / "scripts" / "release_bootstrap.ps1").read_text(encoding="utf-8")

    assert "Windows PowerShell 5.1 compatible" in script
    assert "Python 3.13 x64 primary / 3.12 x64 fallback" in script
    assert "foreach ($selector in @('-3.13', '-3.12'))" in script
    assert "'-3.11'" not in script
    assert "Python.Python.3.13" in script
    assert "Python.Python.3.12" not in script
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


def test_packaged_launcher_requires_current_release_bootstrap_only() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'scripts\\release_bootstrap.ps1' in launcher
    assert 'if not exist "%ROOT%scripts\\release_bootstrap.ps1" goto RELEASE_NO_BOOTSTRAP' in launcher
    assert 'set "RELEASE_BOOTSTRAP=%ROOT%scripts\\release_bootstrap.ps1"' in launcher
    assert "portable_bootstrap" not in launcher
    assert "0.3.6" not in launcher


def test_portable_docs_use_current_python_support_contract() -> None:
    english = (ROOT / "PORTABLE_README.txt").read_text(encoding="utf-8")
    russian = (ROOT / "README_RU.txt").read_text(encoding="utf-8")

    assert "0.4.0" not in english
    assert "0.4.0" not in russian
    assert "Python 3.13 x64 primary; Python 3.12 x64 fallback" in english
    assert "Python 3.11 is not supported" in english
    assert "Python 3.13 x64 — основной; Python 3.12 x64 — совместимый fallback" in russian
    assert "Python 3.11 не поддерживается" in russian
    assert "PyTorch 2.12.1" in english
    assert "PyTorch 2.12.1" in russian
