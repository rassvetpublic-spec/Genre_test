@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "ROOT=%~dp0"
set "VERSION=unknown"
set "MODE=RELEASE"
set "WINPS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if exist "%ROOT%.git" set "MODE=WORKING"
if exist "%ROOT%pyproject.toml" for /f "tokens=3" %%V in ('findstr /b /c:"version = " "%ROOT%pyproject.toml" 2^>nul') do set "VERSION=%%~V"

if /I "%MODE%"=="WORKING" goto WORKING
goto RELEASE

:WORKING
title Genre_test %VERSION% - Working Copy
echo ============================================================
echo   Genre_test %VERSION% - WORKING COPY
echo ============================================================
echo Root   : %ROOT%
echo Mode   : Git working tree
echo Version: %VERSION%
echo.

if /I "%~1"=="retrieval-status" goto WORKING_RETRIEVAL_STATUS
if /I "%~1"=="retrieval-setup" goto WORKING_RETRIEVAL_SETUP
if /I "%~1"=="retrieval-smoke" goto WORKING_RETRIEVAL_SMOKE
if /I "%~1"=="retrieval-direct-smoke" goto WORKING_RETRIEVAL_DIRECT_SMOKE
if /I "%~1"=="retrieval-p0-gate" goto WORKING_RETRIEVAL_P0_GATE
if /I "%~1"=="retrieval-index-status" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="retrieval-index" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="retrieval-rebuild" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="retrieval-search-audio" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="retrieval-search-text" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="retrieval-search-history" goto WORKING_RETRIEVAL_PRODUCT
if /I "%~1"=="help" goto WORKING_HELP
if not "%~1"=="" goto WORKING_UNKNOWN_COMMAND

set "NEED_SETUP=0"
set "INSTALLED_VERSION="
set "PYPROJECT_STAMP="
set "SETUP_STAMP="
set "ENV_STAMP="
set "SAVED_STAMP="
set "STAMP_FILE=%ROOT%.genre_test\launcher_pyproject.stamp"

if not exist "%ROOT%.venv\Scripts\genre-test.exe" set "NEED_SETUP=1"
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" set "NEED_SETUP=1"
if not exist "%ROOT%.venv\Scripts\genre-test-retrieval.exe" set "NEED_SETUP=1"

if exist "%ROOT%.venv\Scripts\genre-test.exe" for /f "tokens=2" %%V in ('"%ROOT%.venv\Scripts\genre-test.exe" --version 2^>nul') do set "INSTALLED_VERSION=%%V"
if /I not "%VERSION%"=="unknown" if /I not "%INSTALLED_VERSION%"=="%VERSION%" set "NEED_SETUP=1"

if exist "%ROOT%pyproject.toml" for %%F in ("%ROOT%pyproject.toml") do set "PYPROJECT_STAMP=%%~zF_%%~tF"
if exist "%ROOT%scripts\setup.ps1" for %%F in ("%ROOT%scripts\setup.ps1") do set "SETUP_STAMP=%%~zF_%%~tF"
if not defined PYPROJECT_STAMP set "NEED_SETUP=1"
if not defined SETUP_STAMP set "NEED_SETUP=1"
if defined PYPROJECT_STAMP if defined SETUP_STAMP set "ENV_STAMP=%PYPROJECT_STAMP%__SETUP__%SETUP_STAMP%"
if not exist "%STAMP_FILE%" set "NEED_SETUP=1"
if exist "%STAMP_FILE%" set /p SAVED_STAMP=<"%STAMP_FILE%"
if defined ENV_STAMP if /I not "%SAVED_STAMP%"=="%ENV_STAMP%" set "NEED_SETUP=1"

if "%NEED_SETUP%"=="0" goto WORKING_GUI

echo [INFO] Working environment needs setup/update.
set "PWSH="
for /f "delims=" %%P in ('where pwsh.exe 2^>nul') do if not defined PWSH set "PWSH=%%P"
if not defined PWSH if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" set "PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
if defined PWSH goto WORKING_HAVE_PWSH

echo [INFO] PowerShell 7 not found. Attempting automatic installation...
if not exist "%WINPS%" goto WORKING_NO_PWSH
if not exist "%ROOT%scripts\ensure_winget.ps1" goto WORKING_NO_PWSH
"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_winget.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto WORKING_NO_PWSH

set "WINGET="
for /f "delims=" %%W in ('where winget.exe 2^>nul') do if not defined WINGET set "WINGET=%%P"
if not defined WINGET if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe" set "WINGET=%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"
if not defined WINGET goto WORKING_NO_PWSH

"%WINGET%" install --id Microsoft.PowerShell --exact --accept-package-agreements --accept-source-agreements
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto WORKING_NO_PWSH

if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" set "PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
if not defined PWSH for /f "delims=" %%P in ('where pwsh.exe 2^>nul') do if not defined PWSH set "PWSH=%%P"
if not defined PWSH goto WORKING_NO_PWSH

:WORKING_HAVE_PWSH
if not exist "%ROOT%scripts\setup.ps1" goto WORKING_NO_SETUP
if exist "%ROOT%scripts\ensure_winget.ps1" "%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_winget.ps1"

echo [INFO] First-run bootstrap reuses Python 3.11/3.12/3.13 x64; installs Python 3.12 x64 only if none is available.
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup.ps1" -InstallPython
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto WORKING_SETUP_FAIL

if not exist "%ROOT%.genre_test" mkdir "%ROOT%.genre_test" >nul 2>&1
set "PYPROJECT_STAMP="
set "SETUP_STAMP="
set "ENV_STAMP="
if exist "%ROOT%pyproject.toml" for %%F in ("%ROOT%pyproject.toml") do set "PYPROJECT_STAMP=%%~zF_%%~tF"
if exist "%ROOT%scripts\setup.ps1" for %%F in ("%ROOT%scripts\setup.ps1") do set "SETUP_STAMP=%%~zF_%%~tF"
if defined PYPROJECT_STAMP if defined SETUP_STAMP set "ENV_STAMP=%PYPROJECT_STAMP%__SETUP__%SETUP_STAMP%"
if defined ENV_STAMP >"%STAMP_FILE%" echo %ENV_STAMP%

:WORKING_GUI
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" goto WORKING_GUI_MISSING
echo [OK] Starting working GUI...
"%ROOT%.venv\Scripts\genre-test-gui.exe"
set "RC=%ERRORLEVEL%"
exit /b %RC%

:WORKING_RETRIEVAL_PREPARE
set "PWSH="nfor /f "delims=" %%P in ('where pwsh.exe 2^>nul') do if not defined PWSH set "PWSH=%%P"
if not defined PWSH if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" set "PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
if not defined PWSH (
  echo [FAIL] PowerShell 7 is required. Run Genre_test_START.cmd once without arguments to bootstrap the core environment.
  exit /b 1
)
if not exist "%ROOT%scripts\setup_clamp3_runtime.ps1" (
  echo [FAIL] Internal retrieval bootstrap is missing: scripts\setup_clamp3_runtime.ps1
  exit /b 1
)
exit /b 0

:WORKING_RETRIEVAL_STATUS
call :WORKING_RETRIEVAL_PREPARE
if errorlevel 1 exit /b 1
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup_clamp3_runtime.ps1"
exit /b %ERRORLEVEL%

:WORKING_RETRIEVAL_SETUP
call :WORKING_RETRIEVAL_PREPARE
if errorlevel 1 exit /b 1
echo [INFO] Preparing optional v0.5 retrieval runtime in flat .genre_test state layout...
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup_clamp3_runtime.ps1" -Install
if errorlevel 1 exit /b %ERRORLEVEL%
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup_clamp3_runtime.ps1" -DownloadModels -AcceptMertNonCommercialTerms
exit /b %ERRORLEVEL%

:WORKING_RETRIEVAL_SMOKE
call :WORKING_RETRIEVAL_PREPARE
if errorlevel 1 exit /b 1
set "RETRIEVAL_AUDIO=%~2"
if not defined RETRIEVAL_AUDIO set /p "RETRIEVAL_AUDIO=Full path to a WAV file: "
if not defined RETRIEVAL_AUDIO (
  echo [FAIL] A WAV path is required.
  exit /b 2
)
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup_clamp3_runtime.ps1" -RunSidecarSmoke -AudioPath "%RETRIEVAL_AUDIO%" -Repeat 2
exit /b %ERRORLEVEL%

:WORKING_RETRIEVAL_DIRECT_SMOKE
call :WORKING_RETRIEVAL_PREPARE
if errorlevel 1 exit /b 1
set "RETRIEVAL_AUDIO=%~2"
if not defined RETRIEVAL_AUDIO set /p "RETRIEVAL_AUDIO=Full path to a WAV file: "
if not defined RETRIEVAL_AUDIO (
  echo [FAIL] A WAV path is required.
  exit /b 2
)
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup_clamp3_runtime.ps1" -RunSmoke -AudioPath "%RETRIEVAL_AUDIO%" -Repeat 2
exit /b %ERRORLEVEL%

:WORKING_RETRIEVAL_P0_GATE
call :WORKING_RETRIEVAL_PREPARE
if errorlevel 1 exit /b 1
set "RETRIEVAL_AUDIO=%~2"
if not defined RETRIEVAL_AUDIO set /p "RETRIEVAL_AUDIO=Full path to a WAV file: "
if not defined RETRIEVAL_AUDIO (
  echo [FAIL] A WAV path is required.
  exit /b 2
)
if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo [FAIL] Core Python is missing. Run Genre_test_START.cmd once without arguments first.
  exit /b 1
)
if not exist "%ROOT%scripts\clamp3_p0_gate.py" (
  echo [FAIL] P0 gate script is missing: scripts\clamp3_p0_gate.py
  exit /b 1
)
echo [INFO] Running complete CLaMP 3 #27/#29 hardware P0 gate...
"%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\clamp3_p0_gate.py" --audio "%RETRIEVAL_AUDIO%" --repeat 2
exit /b %ERRORLEVEL%

:WORKING_RETRIEVAL_PRODUCT
if not exist "%ROOT%.venv\Scripts\genre-test-retrieval.exe" (
  echo [FAIL] Retrieval product CLI is missing from the core venv.
  echo Run Genre_test_START.cmd once without arguments to refresh the working environment.
  exit /b 1
)
"%ROOT%.venv\Scripts\genre-test-retrieval.exe" %*
exit /b %ERRORLEVEL%

:WORKING_HELP
echo Usage:
echo   Genre_test_START.cmd
echo   Genre_test_START.cmd retrieval-status
echo   Genre_test_START.cmd retrieval-setup
echo   Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
echo   Genre_test_START.cmd retrieval-direct-smoke "D:\path\track.wav"
echo   Genre_test_START.cmd retrieval-p0-gate "D:\path\track.wav"
echo   Genre_test_START.cmd retrieval-index-status
echo   Genre_test_START.cmd retrieval-index [--limit N]
echo   Genre_test_START.cmd retrieval-rebuild
echo   Genre_test_START.cmd retrieval-search-audio "D:\path\track.wav" [options]
echo   Genre_test_START.cmd retrieval-search-text "Russian text query" [options]
echo   Genre_test_START.cmd retrieval-search-history [--limit N]
echo.
echo State layout:
echo   .genre_test\logs                    all logs/diagnostics
echo   .genre_test\models                  model assets
echo   .genre_test\runtimes\clamp3        isolated CLaMP runtime
echo   .genre_test\upstream\clamp3        pinned upstream source
echo   .genre_test\retrieval.sqlite3       retrieval cache/index DB when used
echo   .genre_test\retrieval               obsolete; migration removes it
echo.
echo Internal scripts under scripts\ are implementation details, not user entry points.
exit /b 0

:WORKING_UNKNOWN_COMMAND
echo [FAIL] Unknown command: %~1
echo Run Genre_test_START.cmd help
exit /b 2

:WORKING_NO_PWSH
echo [FAIL] PowerShell 7 could not be prepared automatically.
echo Ensure Windows PowerShell 5.1 and WinGet/App Installer are available, then run this launcher again.
echo.
pause
exit /b 1

:WORKING_NO_SETUP
echo [FAIL] scripts\setup.ps1 is missing from the working checkout.
echo.
pause
exit /b 1

:WORKING_SETUP_FAIL
echo.
echo [FAIL] Working environment setup failed. Exit code: %RC%
echo.
pause
exit /b %RC%

:WORKING_GUI_MISSING
echo [FAIL] GUI executable is missing after setup:
echo   %ROOT%.venv\Scripts\genre-test-gui.exe
echo.
pause
exit /b 1

:RELEASE
title Genre_test %VERSION% - Release
echo ============================================================
echo   Genre_test %VERSION% - RELEASE / PORTABLE
echo ============================================================
echo Root   : %ROOT%
echo Mode   : packaged release
echo Version: %VERSION%
echo.

if not exist "%WINPS%" goto RELEASE_NO_WINPS
if not exist "%ROOT%scripts\release_bootstrap.ps1" goto RELEASE_NO_BOOTSTRAP
set "RELEASE_BOOTSTRAP=%ROOT%scripts\release_bootstrap.ps1"

:RELEASE_PREFLIGHT
if exist "%ROOT%scripts\ensure_winget.ps1" "%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_winget.ps1"
if exist "%ROOT%scripts\ensure_vcredist.ps1" "%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_vcredist.ps1"
if errorlevel 1 goto RELEASE_VC_FAIL

echo [INFO] Release bootstrap: %RELEASE_BOOTSTRAP%
"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%RELEASE_BOOTSTRAP%"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" exit /b 0

echo.
echo [FAIL] Genre_test release could not be started.
echo See diagnostics under: %ROOT%.genre_test\logs\
echo.
pause
exit /b %RC%

:RELEASE_NO_WINPS
echo [FAIL] Windows PowerShell 5.1 was not found.
echo.
pause
exit /b 1

:RELEASE_NO_BOOTSTRAP
echo [FAIL] scripts\release_bootstrap.ps1 is missing from this release package.
echo.
pause
exit /b 1

:RELEASE_VC_FAIL
echo [FAIL] Microsoft Visual C++ x64 Runtime could not be prepared.
echo.
pause
exit /b 1