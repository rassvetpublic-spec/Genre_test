@echo off
setlocal
cd /d "%~dp0"
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\repo-governance.ps1" -Mode Check
exit /b %ERRORLEVEL%
