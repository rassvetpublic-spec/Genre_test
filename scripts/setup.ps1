#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$Cpu,
    [switch]$InstallPython,
    [switch]$SkipFFmpeg
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

function Test-PythonVersion {
    param(
        [Parameter(Mandatory)] [string]$Exe,
        [string[]]$PrefixArgs = @()
    )

    try {
        $versionText = & $Exe @PrefixArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        $version = [version]($versionText | Select-Object -Last 1)
        if ($version.Major -eq 3 -and $version.Minor -ge 11 -and $version.Minor -lt 13) {
            return $version
        }
    }
    catch {
        return $null
    }
    return $null
}

function Find-CompatiblePython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($selector in @('-3.12', '-3.11')) {
            $v = Test-PythonVersion -Exe $py.Source -PrefixArgs @($selector)
            if ($v) {
                return [pscustomobject]@{
                    Exe = $py.Source
                    PrefixArgs = @($selector)
                    Version = $v
                    Display = "py $selector"
                }
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $v = Test-PythonVersion -Exe $python.Source
        if ($v) {
            return [pscustomobject]@{
                Exe = $python.Source
                PrefixArgs = @()
                Version = $v
                Display = $python.Source
            }
        }
    }

    return $null
}

$runtime = Find-CompatiblePython

if (-not $runtime -and $InstallPython) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'Python 3.11/3.12 is missing and winget is unavailable. Install Python 3.12 x64, then rerun setup.ps1.'
    }

    Write-Host 'Python 3.11/3.12 not found. Installing Python 3.12 x64 with winget...'
    & $winget.Source install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed to install Python 3.12 (exit code $LASTEXITCODE)."
    }

    $runtime = Find-CompatiblePython
    if (-not $runtime) {
        throw @'
Python 3.12 was installed, but this PowerShell session cannot see it yet.
Close this terminal, open PowerShell 7 again, then run:
  cd C:\GIT\Genre_test
  .\scripts\setup.ps1
'@
    }
}

if (-not $runtime) {
    throw @'
Compatible Python not found. Genre_test requires Python 3.11 or 3.12 x64.

Recommended automatic install:
  .\scripts\setup.ps1 -InstallPython

Or install manually:
  winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements

Then open a new PowerShell 7 window and verify:
  py -0p
  py -3.12 --version

Finally rerun:
  cd C:\GIT\Genre_test
  .\scripts\setup.ps1
'@
}

Write-Host "Using Python $($runtime.Version): $($runtime.Display)"

$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if ((Test-Path (Join-Path $repoRoot '.venv')) -and -not (Test-Path $venvPython)) {
    Write-Warning 'Broken or incomplete .venv detected. Removing it.'
    Remove-Item -Recurse -Force (Join-Path $repoRoot '.venv')
}

if (-not (Test-Path $venvPython)) {
    Write-Host 'Creating virtual environment...'
    $venvArgs = @($runtime.PrefixArgs) + @('-m', 'venv', (Join-Path $repoRoot '.venv'))
    & $runtime.Exe @venvArgs
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        throw 'Virtual environment creation failed.'
    }
}

& $venvPython -m pip install --upgrade pip wheel

if ($Cpu) {
    Write-Host 'Installing CPU PyTorch...'
    & $venvPython -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cpu
}
elseif (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host 'NVIDIA GPU detected. Installing CUDA 12.8 PyTorch wheel...'
    & $venvPython -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
}
else {
    Write-Host 'NVIDIA GPU not detected. Installing default PyTorch package...'
    & $venvPython -m pip install --upgrade torch
}

& $venvPython -m pip install -e '.[dev]'

if (-not $SkipFFmpeg) {
    Write-Host "`nChecking FFmpeg..."
    $ensureFFmpeg = Join-Path $PSScriptRoot 'ensure_ffmpeg.ps1'
    if ($IsWindows) {
        & $ensureFFmpeg -Required
    }
    else {
        & $ensureFFmpeg
    }
}
else {
    Write-Warning 'FFmpeg bootstrap skipped by -SkipFFmpeg.'
}

Write-Host "`nInstalled. Checking runtime..."
$genreExe = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
if (-not (Test-Path $genreExe)) {
    throw "Installation completed but CLI executable was not created: $genreExe"
}
& $genreExe doctor

Write-Host "`nSetup complete. First analysis downloads the MAEST model into the Hugging Face cache."
Write-Host "GUI: .\scripts\gui.ps1  (or double-click scripts\Genre_test_GUI.cmd)"
