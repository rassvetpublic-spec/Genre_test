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
set "PYPROJECT_HASH="
set "SAVED_HASH="
set "HASH_FILE=%ROOT%.genre_test\launcher_pyproject.sha256"

if not exist "%ROOT%.venv\Scripts\genre-test.exe" set "NEED_SETUP=1"
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" set "NEED_SETUP=1"

if not exist "%ROOT%.venv\Scripts\genre-test.exe" goto WORKING_HASH
for /f "tokens=2" %%V in ('"%ROOT%.venv\Scripts\genre-test.exe" --version 2^>nul') do set "INSTALLED_VERSION=%%V"
if /I not "%VERSION%"=="unknown" if /I not "%INSTALLED_VERSION%"=="%VERSION%" set "NEED_SETUP=1"

:WORKING_HASH
if not exist "%ROOT%pyproject.toml" goto WORKING_SETUP
if not exist "%WINPS%" goto WORKING_SETUP
set "GENRE_TEST_LAUNCH_ROOT=%ROOT%"
for /f "usebackq delims=" %%H in (`"%WINPS%" -NoLogo -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $env:GENRE_TEST_LAUNCH_ROOT 'pyproject.toml')).Hash"`) do set "PYPROJECT_HASH=%%H"
if not defined PYPROJECT_HASH set "NEED_SETUP=1"
if not exist "%HASH_FILE%" set "NEED_SETUP=1"
if not exist "%HASH_FILE%" goto WORKING_SETUP
set /p SAVED_HASH=<"%HASH_FILE%"
if /I not "%SAVED_HASH%"=="%PYPROJECT_HASH%" set "NEED_SETUP=1"

:WORKING_SETUP
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
if not defined PYPROJECT_HASH goto WORKING_REHASH
goto WORKING_SAVE_HASH

:WORKING_REHASH
if not exist "%WINPS%" goto WORKING_GUI
set "GENRE_TEST_LAUNCH_ROOT=%ROOT%"
for /f "usebackq delims=" %%H in (`"%WINPS%" -NoLogo -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $env:GENRE_TEST_LAUNCH_ROOT 'pyproject.toml')).Hash"`) do set "PYPROJECT_HASH=%%H"

:WORKING_SAVE_HASH
if defined PYPROJECT_HASH >"%HASH_FILE%" echo %PYPROJECT_HASH%

:WORKING_GUI
if not exist "%ROOT%.venv\Scripts\genre-test-gui.exe" goto WORKING_GUI_MISSING
echo [OK] Starting working GUI...
"%ROOT%.venv\Scripts\genre-test-gui.exe"
set "RC=%ERRORLEVEL%"
exit /b %RC%

:WORKING_NO_PWSH
echo [FAIL] PowerShell 7 ^(pwsh.exe^) is required to prepare a working checkout.
echo Install PowerShell 7 or run the already prepared .venv GUI directly.
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
if not exist "%ROOT%scripts\ensure_winget.ps1" goto RELEASE_VC
"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_winget.ps1"
set "WINGET_RC=%ERRORLEVEL%"
if "%WINGET_RC%"=="0" goto RELEASE_VC
echo.
echo [WARN] WinGet could not be restored automatically.
echo Bootstrap will continue and only require it if a dependency is missing.
echo.

:RELEASE_VC
if not exist "%ROOT%scripts\ensure_vcredist.ps1" goto RELEASE_BOOTSTRAP_RUN
"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\ensure_vcredist.ps1"
set "VC_RC=%ERRORLEVEL%"
if not "%VC_RC%"=="0" goto RELEASE_VC_FAIL

:RELEASE_BOOTSTRAP_RUN
echo [INFO] Release bootstrap: %RELEASE_BOOTSTRAP%
"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%RELEASE_BOOTSTRAP%"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" exit /b 0

echo.
echo ============================================================
echo [FAIL] Genre_test release could not be started.
echo ============================================================
echo See diagnostics under:
echo   %ROOT%.genre_test\
echo.
pause
exit /b %RC%

:RELEASE_NO_WINPS
echo [FAIL] Windows PowerShell 5.1 was not found.
echo This release requires Windows 10 or Windows 11 x64.
echo.
pause
exit /b 1

:RELEASE_NO_BOOTSTRAP
echo [FAIL] No bootstrap matches Genre_test release %VERSION%.
echo.
echo Current releases must contain:
echo   scripts\release_bootstrap.ps1
echo.
echo Legacy scripts\portable_bootstrap_v2.ps1 is accepted only for 0.3.6.
echo This guard prevents a 0.4+ release from silently installing the old CUDA 12.8 runtime.
echo.
pause
exit /b 1

:RELEASE_VC_FAIL
echo.
echo [FAIL] Microsoft Visual C++ x64 Runtime could not be prepared.
echo.
pause
exit /b %VC_RC%
