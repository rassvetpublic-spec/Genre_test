#requires -Version 7.0
param(
    [switch]$Cpu
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher (py.exe) not found. Install Python 3.11 x64 first."
}

if (-not (Test-Path .venv)) {
    py -3.11 -m venv .venv
}

$python = Join-Path $PWD '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip wheel

if ($Cpu) {
    Write-Host 'Installing CPU PyTorch...'
    & $python -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cpu
}
elseif (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host 'NVIDIA GPU detected. Installing CUDA 12.8 PyTorch wheel...'
    & $python -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
}
else {
    Write-Host 'NVIDIA GPU not detected. Installing default PyTorch package...'
    & $python -m pip install --upgrade torch
}

& $python -m pip install -e '.[dev]'

Write-Host "\nInstalled. Checking runtime..."
& (Join-Path $PWD '.venv\Scripts\genre-test.exe') doctor
Write-Host "\nFirst analysis downloads the MAEST model into the Hugging Face cache."
