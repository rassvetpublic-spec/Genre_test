#requires -Version 7.0
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$genreTest = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'

if (-not (Test-Path $python)) {
    throw 'Existing .venv not found. Run .\scripts\setup.ps1 instead.'
}

Write-Host 'Installing current Genre_test from this checkout...'
& $python -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) {
    throw 'Upgrade install failed.'
}

Write-Host "`nRuntime check:"
& $genreTest doctor
if ($LASTEXITCODE -ne 0) {
    throw 'genre-test doctor failed.'
}

Write-Host "`nUpgrade complete."
Write-Host 'GUI: .\scripts\gui.ps1'
Write-Host 'Validation: open the Validation / Перепроверка tab in the GUI.'
