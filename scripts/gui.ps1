#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$guiExe = Join-Path $repoRoot '.venv\Scripts\genre-test-gui.exe'
if (-not (Test-Path $guiExe)) {
    throw "GUI executable not found. Run .\scripts\setup.ps1 first."
}
& $guiExe
