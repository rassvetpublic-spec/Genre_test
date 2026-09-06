@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "LESSCHARSET=utf-8"
cd /d "%~dp0.."
if not exist ".venv\Scripts\genre-test-gui.exe" (
  echo Genre_test is not installed. Run scripts\setup.ps1 first.
  pause
  exit /b 1
)
start "Genre_test" ".venv\Scripts\genre-test-gui.exe"
