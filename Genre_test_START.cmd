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

set "NEED_SETUP=0"
set "INSTALLED_VERSION="
set "PYPROJECT_STAMP="
set "SAVED_STAMP="
set "STAMP_FILE=%ROOT%.genre_test\launcher_pyproject.stamp"

if not exist "%ROOT%.venv\Scripts\genre-test.exe" set "NEED_SETUP=1"
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" set "NEED_SETUP=1"

if exist "%ROOT%.venv\Scripts\genre-test.exe" for /f "tokens=2" %%V in ('"%ROOT%.venv\Scripts\genre-test.exe" --version 2^>nul') do set "INSTALLED_VERSION=%%V"
if /I not "%VERSION%"=="unknown" if /I not "%INSTALLED_VERSION%"=="%VERSION%" set "NEED_SETUP=1"

if exist "%ROOT%pyproject.toml" for %%F in ("%ROOT%pyproject.toml") do set "PYPROJECT_STAMP=%%~zF_%%~tF"
if not defined PYPROJECT_STAMP set "NEED_SETUP=1"
if not exist "%STAMP_FILE%" set "NEED_SETUP=1"
if exist "%STAMP_FILE%" set /p SAVED_STAMP=<"%STAMP_FILE%"
if defined PYPROJECT_STAMP if /I not "%SAVED_STAMP%"=="%PYPROJECT_STAMP%" set "NEED_SETUP=1"

if "%NEED_SETUP%"=="0" goto WORKING_GUI

echo [INFO] Working environment needs setup/update.
set "PWSH="
for /f "delims=" %%P in ('where pwsh.exe 2^>nul') do if not defined PWSH set "PWSH=%%P"
if not defined PWSH goto WORKING_NO_PWSH
if not exist "%ROOT%scripts\setup.ps1" goto WORKING_NO_SETUP

"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto WORKING_SETUP_FAIL

if not exist "%ROOT%.genre_test" mkdir "%ROOT%.genre_test" >nul 2>&1
if exist "%ROOT%pyproject.toml" for %%F in ("%ROOT%pyproject.toml") do set "PYPROJECT_STAMP=%%~zF_%%~tF"
if defined PYPROJECT_STAMP >"%STAMP_FILE%" echo %PYPROJECT_STAMP%

:WORKING_GUI
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" goto WORKING_GUI_MISSING
echo [OK] Starting working GUI...
"%ROOT%.venv\Scripts\genre-test-gui.exe"
set "RC=%ERRORLEVEL%"
exit /b %RC%

:WORKING_NO_PWSH
echo [FAIL] PowerShell 7 ^(pwsh.exe^) is required to prepare a working checkout.
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

set "RELEASE_BOOTSTRAP="
if exist "%ROOT%scripts\release_bootstrap.ps1" set "RELEASE_BOOTSTRAP=%ROOT%scripts\release_bootstrap.ps1"
if defined RELEASE_BOOTSTRAP goto RELEASE_PREFLIGHT
if /I "%VERSION%"=="0.3.6" if exist "%ROOT%scripts\portable_bootstrap_v2.ps1" set "RELEASE_BOOTSTRAP=%ROOT%scripts\portable_bootstrap_v2.ps1"
if not defined RELEASE_BOOTSTRAP goto RELEASE_NO_BOOTSTRAP

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
echo See diagnostics under: %ROOT%.genre_test\
echo.
pause
exit /b %RC%

:RELEASE_NO_WINPS
echo [FAIL] Windows PowerShell 5.1 was not found.
echo.
pause
exit /b 1

:RELEASE_NO_BOOTSTRAP
echo [FAIL] No bootstrap matches Genre_test release %VERSION%.
echo Current releases must contain scripts\release_bootstrap.ps1.
echo Legacy portable_bootstrap_v2.ps1 is accepted only for 0.3.6.
echo.
pause
exit /b 1

:RELEASE_VC_FAIL
echo [FAIL] Microsoft Visual C++ x64 Runtime could not be prepared.
echo.
pause
exit /b 1
