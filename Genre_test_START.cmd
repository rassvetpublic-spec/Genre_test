@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Genre_test 0.3.6 Portable
cd /d "%~dp0"

echo ============================================================
echo   Genre_test 0.3.6 Portable - Setup / Diagnostics / GUI
echo ============================================================
echo.

set "EXPECTED=C:\Genre_test_0.3.6_portable\"
if /I not "%~dp0"=="%EXPECTED%" (
    echo [FAIL] Wrong installation folder.
    echo.
    echo Extract the ZIP directly to C:\ so that this file is located at:
    echo   C:\Genre_test_0.3.6_portable\Genre_test_START.cmd
    echo.
    echo Current folder:
    echo   %~dp0
    echo.
    echo Do not run the package from Downloads, Desktop, D:\ or inside the ZIP.
    echo.
    pause
    exit /b 2
)

set "WINPS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%WINPS%" (
    echo [FAIL] Windows PowerShell was not found.
    echo This package requires Windows 10 or Windows 11 x64.
    echo.
    pause
    exit /b 1
)

"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ensure_winget.ps1"
set "WINGET_RC=%ERRORLEVEL%"
if not "%WINGET_RC%"=="0" (
    echo.
    echo [WARN] WinGet could not be restored automatically.
    echo The main bootstrap will continue and only require WinGet if
    echo Python, VC++ Runtime or FFmpeg actually needs installation.
    echo.
)

"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ensure_vcredist.ps1"
set "VC_RC=%ERRORLEVEL%"
if not "%VC_RC%"=="0" (
    echo.
    echo [FAIL] Microsoft Visual C++ x64 Runtime could not be prepared.
    echo.
    pause
    exit /b %VC_RC%
)

"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\portable_bootstrap_v2.ps1"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo ============================================================
    echo [FAIL] Genre_test could not be started.
    echo ============================================================
    echo.
    echo See these files for details:
    echo   C:\Genre_test_0.3.6_portable\.genre_test\bootstrap.log
    echo   C:\Genre_test_0.3.6_portable\.genre_test\torch_import_diagnostic.txt
    echo   C:\Genre_test_0.3.6_portable\.genre_test\torch_probe_stdout.txt
    echo.
    pause
    exit /b %RC%
)

exit /b 0
