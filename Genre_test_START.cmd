@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Genre_test 0.3.6 Portable
cd /d "%~dp0"

echo ============================================================
echo   Genre_test 0.3.6 Portable - Setup / Diagnostics / GUI
echo ============================================================
echo.

set "WINPS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%WINPS%" (
    echo [FAIL] Windows PowerShell was not found.
    echo This package requires Windows 10 or Windows 11 x64.
    echo.
    pause
    exit /b 1
)

"%WINPS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\portable_bootstrap.ps1"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo ============================================================
    echo [FAIL] Genre_test could not be started.
    echo See .genre_test\bootstrap.log for details.
    echo ============================================================
    echo.
    pause
    exit /b %RC%
)

exit /b 0
