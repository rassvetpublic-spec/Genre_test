#requires -Version 7.0
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Run scripts/setup.ps1 first.' }
& $python -m ruff check src tests
& $python -m pytest -q
