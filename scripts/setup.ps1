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

$TorchVersion = '2.12.1'
$CudaIndex = 'https://download.pytorch.org/whl/cu130'
$CpuIndex = 'https://download.pytorch.org/whl/cpu'

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

function Get-TorchProbe {
    param([Parameter(Mandatory)] [string]$Python)

    $code = @'
import sys
try:
    import torch
    raw = str(torch.__version__)
    nums = raw.split('+', 1)[0].split('.')[:3]
    ver = tuple(int(''.join(ch for ch in x if ch.isdigit()) or '0') for x in nums)
    while len(ver) < 3:
        ver = ver + (0,)
    available = bool(torch.cuda.is_available())
    cuda = str(torch.version.cuda or 'none')
    gpu = 'cpu'
    arch = 'none'
    native = True
    blackwell = False
    if available:
        gpu = str(torch.cuda.get_device_name(0))
        major, minor = torch.cuda.get_device_capability(0)
        arch = f'sm_{major}{minor}'
        native = arch in set(torch.cuda.get_arch_list())
        blackwell = major in {10, 11, 12}
    version_ok = ver >= (2, 12, 1)
    cuda_ok = (not available) or cuda.startswith('13.0')
    native_ok = (not blackwell) or native
    ok = version_ok and cuda_ok and native_ok
    print(f'__GT_TORCH__|{raw}|{cuda}|{available}|{gpu}|{arch}|{native}|{blackwell}|{ok}')
except Exception as exc:
    print(f'__GT_TORCH_ERROR__|{type(exc).__name__}|{exc}')
    sys.exit(2)
'@

    try {
        $line = (& $Python -c $code 2>$null | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or -not $line -or $line -notlike '__GT_TORCH__|*') {
            return $null
        }
        $parts = [string]$line -split '\|'
        return [pscustomobject]@{
            Version = $parts[1]
            Cuda = $parts[2]
            Available = [bool]::Parse($parts[3])
            Gpu = $parts[4]
            Architecture = $parts[5]
            Native = [bool]::Parse($parts[6])
            Blackwell = [bool]::Parse($parts[7])
            TargetOK = [bool]::Parse($parts[8])
        }
    }
    catch {
        return $null
    }
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

& $venvPython -m pip install --upgrade pip wheel 'setuptools<82'
if ($LASTEXITCODE -ne 0) { throw 'pip bootstrap failed.' }

try {
    $pipCache = (& $venvPython -m pip cache dir 2>$null | Select-Object -Last 1)
    if ($pipCache) { Write-Host "Shared pip wheel cache: $pipCache" }
}
catch {}

$existing = Get-TorchProbe -Python $venvPython
$hasNvidia = [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)

if ($Cpu) {
    if ($existing -and -not $existing.Available -and ([version]($existing.Version.Split('+')[0]) -ge [version]'2.12.1')) {
        Write-Host "Compatible CPU PyTorch already installed: $($existing.Version). Skipping reinstall."
    }
    else {
        Write-Host "Installing CPU PyTorch $TorchVersion..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CpuIndex
        if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed.' }
    }
}
elif ($hasNvidia) {
    if ($existing -and $existing.TargetOK -and $existing.Available) {
        Write-Host "Compatible PyTorch already installed: $($existing.Version), CUDA $($existing.Cuda), $($existing.Architecture), native=$($existing.Native)."
        Write-Host 'Skipping the multi-GB PyTorch reinstall.'
    }
    else {
        Write-Host "NVIDIA GPU detected. Installing PyTorch $TorchVersion / CUDA 13.0..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CudaIndex
        if ($LASTEXITCODE -ne 0) { throw 'CUDA 13.0 PyTorch installation failed.' }
    }
}
else {
    if ($existing -and ([version]($existing.Version.Split('+')[0]) -ge [version]'2.12.1')) {
        Write-Host "Compatible PyTorch already installed: $($existing.Version). Skipping reinstall."
    }
    else {
        Write-Host "NVIDIA GPU not detected. Installing CPU PyTorch $TorchVersion..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CpuIndex
        if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed.' }
    }
}

$probe = Get-TorchProbe -Python $venvPython
if (-not $probe) {
    throw 'PyTorch cannot be imported after installation.'
}
if ($hasNvidia -and -not $Cpu -and -not $probe.TargetOK) {
    throw "GPU runtime does not meet v0.4 target: torch=$($probe.Version), CUDA=$($probe.Cuda), arch=$($probe.Architecture), native=$($probe.Native)."
}
Write-Host "PyTorch runtime: $($probe.Version) | CUDA $($probe.Cuda) | $($probe.Gpu) | $($probe.Architecture) | native=$($probe.Native)"

& $venvPython -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Genre_test dependency installation failed.' }

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
if ($LASTEXITCODE -ne 0) { throw 'genre-test doctor failed.' }

Write-Host "`nSetup complete. GPU baseline: PyTorch >=2.12.1 / CUDA 13.0 / native Blackwell when applicable."
Write-Host "GUI: .\scripts\gui.ps1  (or double-click scripts\Genre_test_GUI.cmd)"
