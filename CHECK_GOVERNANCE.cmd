@echo off
setlocal
cd /d "%~dp0"

pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\github-settings.ps1" -Mode Check
if errorlevel 1 exit /b %ERRORLEVEL%

git config --get core.hooksPath | findstr /x /c:".githooks" >nul
if errorlevel 1 (
    echo FAIL local core.hooksPath is not .githooks
    exit /b 2
)

if not exist ".githooks\pre-push" (
    echo FAIL .githooks\pre-push is missing
    exit /b 2
)

echo PASS permanent repository governance checks
exit /b 0