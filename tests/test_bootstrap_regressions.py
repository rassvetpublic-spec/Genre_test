from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_launcher_fingerprint_includes_pyproject_and_setup_script():
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'set "PYPROJECT_STAMP="' in launcher
    assert 'set "SETUP_STAMP="' in launcher
    assert 'set "ENV_STAMP="' in launcher
    assert 'scripts\\setup.ps1") do set "SETUP_STAMP=%%~zF_%%~tF"' in launcher
    assert "%PYPROJECT_STAMP%__SETUP__%SETUP_STAMP%" in launcher
    assert "launcher_pyproject.stamp" in launcher


def test_core_setup_prefers_python313_and_retires_python311():
    setup = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")

    assert "foreach ($selector in @('-3.13', '-3.12'))" in setup
    assert "'-3.11'" not in setup
    assert "^3\\.(12|13)\\|64$" in setup
    assert "Python.Python.3.13" in setup
    assert "Python.Python.3.12" not in setup
    assert "Python 3.11 is unsupported" in setup
    assert "Python 3.13 x64 (primary); Python 3.12 x64 (fallback)" in launcher
    assert "Python 3.11/3.12/3.13" not in launcher


def test_core_setup_recreates_an_existing_unsupported_virtualenv():
    setup = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")

    assert "if (Test-Path $venvPython)" in setup
    assert "$venvVersion -notmatch '^3\\.(12|13)\\|64$'" in setup
    assert "Existing .venv uses unsupported Python" in setup
    assert "Recreating it with Python $($runtime.Version)" in setup
    assert "Remove-Item -Recurse -Force $venvDir" in setup


def test_setup_detects_nvidia_hardware_even_when_nvidia_smi_is_not_on_path():
    setup = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    assert "function Test-NvidiaHardware" in setup
    assert "Get-Command nvidia-smi" in setup
    assert "Win32_VideoController" in setup
    assert "VEN_10DE" in setup
    assert "$hasNvidia = Test-NvidiaHardware" in setup
    assert "NVIDIA hardware is present but CUDA runtime is unavailable/incompatible" in setup


def test_successful_winget_bootstrap_returns_to_calling_setup():
    helper = (ROOT / "scripts" / "ensure_winget.ps1").read_text(encoding="utf-8")
    assert "exit 0" not in helper
    assert 'Write-Host "WinGet OK: $existing"\n    return' in helper
    assert 'Write-Host "WinGet repaired successfully: $winget"' in helper
    assert "& $winget --version\n        return" in helper
    assert "exit 2" in helper
