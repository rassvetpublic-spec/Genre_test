@echo off
setlocal
cd /d "%~dp0"

set "PYEXE="

py -3.13 -c "import sys; print(sys.executable)" >nul 2>nul
if not errorlevel 1 set "PYEXE=py -3.13"

if not defined PYEXE (
  py -3.12 -c "import sys; print(sys.executable)" >nul 2>nul
  if not errorlevel 1 set "PYEXE=py -3.12"
)

if not defined PYEXE (
  python -c "import sys; print(sys.executable)" >nul 2>nul
  if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
  echo ERROR: Python 3.13/3.12 or python launcher not found.
  exit /b 2
)

%PYEXE% tools\check_markdown_authoring.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo Markdown authoring check FAILED with code %RC%.
  exit /b %RC%
)

%PYEXE% tools\obsidian_knowledge_sync.py --check
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo Obsidian knowledge check FAILED with code %RC%.
  exit /b %RC%
)

echo Obsidian + Markdown authoring checks PASS.
exit /b 0
