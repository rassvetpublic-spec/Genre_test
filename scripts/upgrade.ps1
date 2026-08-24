#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$SkipFFmpeg
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Existing .venv not found. Run .\scripts\setup.ps1 instead.'
}

Write-Host 'Upgrading Genre_test and validating the v0.4 GPU runtime...'
$setup = Join-Path $PSScriptRoot 'setup.ps1'
& $setup -SkipFFmpeg
if ($LASTEXITCODE -ne 0) {
    throw 'setup.ps1 runtime upgrade failed.'
}

if (-not $SkipFFmpeg) {
    Write-Host "`nChecking FFmpeg..."
    $ensureFFmpeg = Join-Path $PSScriptRoot 'ensure_ffmpeg.ps1'
    if ($IsWindows) { & $ensureFFmpeg -Required } else { & $ensureFFmpeg }
} else {
    Write-Warning 'FFmpeg bootstrap skipped by -SkipFFmpeg.'
}

$genreTest = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
Write-Host "`nFinal runtime check:"
& $genreTest doctor
if ($LASTEXITCODE -ne 0) {
    throw 'genre-test doctor failed.'
}

Write-Host "`nUpgrade complete."
Write-Host 'GPU target: PyTorch >=2.12.1 / CUDA 13.0 / native Blackwell when applicable.'
Write-Host 'GUI: .\scripts\gui.ps1'
