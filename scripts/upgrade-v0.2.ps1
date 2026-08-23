#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Existing .venv not found. Run .\scripts\setup.ps1 instead.'
}
& $python -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Upgrade install failed.' }
& (Join-Path $repoRoot '.venv\Scripts\genre-test.exe') doctor
Write-Host "`nUpgrade to Genre_test 0.2.0 complete."
Write-Host "GUI: .\scripts\gui.ps1"
