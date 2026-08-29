@echo off
setlocal
cd /d "%~dp0"

pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\github-settings.ps1" -Mode Check
if errorlevel 1 exit /b %ERRORLEVEL%

set "HOOKSPATH="
for /f "usebackq delims=" %%H in (`git config --local --get core.hooksPath 2^>nul`) do set "HOOKSPATH=%%H"
if /I not "%HOOKSPATH%"==".githooks" (
    echo FAIL local core.hooksPath is not .githooks ^(actual: "%HOOKSPATH%"^)
    exit /b 2
)

if not exist ".githooks\pre-push" (
    echo FAIL .githooks\pre-push is missing
    exit /b 2
)

echo PASS permanent repository governance checks
exit /b 0
