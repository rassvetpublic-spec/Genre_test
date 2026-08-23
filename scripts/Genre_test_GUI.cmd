@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\genre-test-gui.exe" (
  echo Genre_test is not installed. Run scripts\setup.ps1 first.
  pause
  exit /b 1
)
start "Genre_test" ".venv\Scripts\genre-test-gui.exe"
