# Windows PowerShell 5.1 compatible one-click bootstrap for Genre_test 0.4.0 release.
[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot
$stateDir = Join-Path $repoRoot '.genre_test'
$logPath = Join-Path $stateDir 'bootstrap.log'
$torchDiagnosticPath = Join-Path $stateDir 'torch_import_diagnostic.txt'
$torchVersion = '2.12.1'
$cudaIndex = 'https://download.pytorch.org/whl/cu130'
$cpuIndex = 'https://download.pytorch.org/whl/cpu'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Write-BootstrapLog {
    param([Parameter(Mandatory=$true)][string]$Message)
    Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] $Message"
}

function Write-Step {
    param([Parameter(Mandatory=$true)][string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
    Write-BootstrapLog $Message
}

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @()
    if ($machine) { $parts += $machine }
    if ($user) { $parts += $user }
    if ($parts.Count -gt 0) { $env:Path = ($parts -join ';') }
}

function Find-Winget {
    Refresh-ProcessPath
    $command = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command winget -ErrorAction SilentlyContinue }
    if ($command) { return [string]$command.Source }
    if ($env:LOCALAPPDATA) {
        $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return [string]$candidate }
    }
    return $null
}

function Require-Winget {
    $winget = Find-Winget
    if ($winget) { return [string]$winget }
    $helper = Join-Path $PSScriptRoot 'ensure_winget.ps1'
    if (Test-Path -LiteralPath $helper) {
        Write-Host 'WinGet not found. Attempting automatic repair...'
        & $helper
        Refresh-ProcessPath
        $winget = Find-Winget
        if ($winget) { return [string]$winget }
    }
    throw 'WinGet is required to install a missing release dependency.'
}

function Invoke-WingetInstall {
    param(
        [Parameter(Mandatory=$true)][string]$Id,
        [switch]$UserScope
    )
    $winget = Require-Winget
    $args = @('install', '--id', $Id, '--exact', '--source', 'winget', '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity')
    if ($UserScope) { $args += @('--scope', 'user') }
    & $winget @args | Out-Host
    $code = $LASTEXITCODE
    if ($code -ne 0 -and $code -ne 3010) { throw "winget failed to install $Id (exit code $code)." }
    Refresh-ProcessPath
}

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [string[]]$PrefixArgs = @()
    )
    try {
        $code = "import sys,struct; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'|'+str(struct.calcsize('P')*8))"
        $args = @($PrefixArgs) + @('-c', $code)
        $text = (& $Exe @args 2>$null | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or -not $text) { return $null }
        $parts = [string]$text -split '\|'
        if ($parts.Count -ne 2) { return $null }
        $version = [version]$parts[0]
        $bits = [int]$parts[1]
        if ($version.Major -eq 3 -and $version.Minor -ge 12 -and $version.Minor -le 13 -and $bits -eq 64) {
            return [pscustomobject]@{ Exe=[string]$Exe; PrefixArgs=@($PrefixArgs); Version=$version; Bits=$bits }
        }
    } catch {}
    return $null
}

function Find-CompatiblePython {
    Refresh-ProcessPath
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        foreach ($selector in @('-3.13', '-3.12')) {
            $found = Test-PythonCandidate -Exe $py.Source -PrefixArgs @($selector)
            if ($found) { return $found }
        }
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
    if ($python) {
        $found = Test-PythonCandidate -Exe $python.Source
        if ($found) { return $found }
    }
    return $null
}

function Ensure-Python {
    Write-Step 'Checking Python 3.13 x64 primary / 3.12 x64 fallback'
    $runtime = Find-CompatiblePython
    if (-not $runtime) {
        Write-Host 'Compatible Python was not found. Installing primary Python 3.13 x64...'
        Invoke-WingetInstall -Id 'Python.Python.3.13' -UserScope
        Start-Sleep -Seconds 1
        $runtime = Find-CompatiblePython
    }
    if (-not $runtime) { throw 'Compatible Python 3.12/3.13 x64 could not be prepared. Python 3.11 is unsupported.' }
    Write-Host "Python OK: $($runtime.Version) x64"
    Write-BootstrapLog "Python=$($runtime.Version) x64"
    return $runtime
}

function Ensure-Venv {
    param([Parameter(Mandatory=$true)]$Runtime)
    $venvDir = Join-Path $repoRoot '.venv'
    $venvPython = Join-Path $venvDir 'Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython) {
        $valid = Test-PythonCandidate -Exe $venvPython
        if (-not $valid) { Remove-Item -LiteralPath $venvDir -Recurse -Force }
    } elseif (Test-Path -LiteralPath $venvDir) {
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Step 'Creating private .venv'
        $args = @($Runtime.PrefixArgs) + @('-m', 'venv', $venvDir)
        & $Runtime.Exe @args | Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) { throw 'Virtual environment creation failed.' }
    }
    return [string]$venvPython
}

function Test-NvidiaHardware {
    Refresh-ProcessPath
    if (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue) { return $true }
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { return $true }
    try {
        $controllers = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop
        foreach ($controller in $controllers) {
            if ([string]$controller.Name -match 'NVIDIA' -or [string]$controller.PNPDeviceID -match 'VEN_10DE') { return $true }
        }
    } catch {}
    try {
        $display = Get-CimInstance -ClassName Win32_PnPEntity -ErrorAction Stop | Where-Object { [string]$_.PNPClass -eq 'Display' }
        foreach ($device in $display) {
            if ([string]$device.PNPDeviceID -match 'VEN_10DE') { return $true }
        }
    } catch {}
    return $false
}

function Get-TorchState {
    param([Parameter(Mandatory=$true)][string]$Python)
    $code = @'
import sys
try:
    import torch
    raw = str(torch.__version__)
    base = raw.split('+', 1)[0]
    version_ok = tuple(int(x) for x in base.split('.')[:3]) >= (2, 12, 1)
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
        blackwell = major in {10, 11, 12}
        native = arch in set(torch.cuda.get_arch_list())
    target = version_ok and ((not available) or cuda.startswith('13.0')) and ((not blackwell) or native)
    print(f'__GT_TORCH__|{raw}|{cuda}|{available}|{gpu}|{arch}|{native}|{blackwell}|{target}')
except Exception as exc:
    print(f'__GT_TORCH_ERROR__|{type(exc).__name__}|{exc}')
    sys.exit(2)
'@
    try {
        $line = (& $Python -c $code 2> $torchDiagnosticPath | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or -not $line -or $line -notlike '__GT_TORCH__|*') { return $null }
        $parts = [string]$line -split '\|'
        return [pscustomobject]@{
            Version=$parts[1]; Cuda=$parts[2]; Available=[bool]::Parse($parts[3]); Gpu=$parts[4]; Architecture=$parts[5];
            Native=[bool]::Parse($parts[6]); Blackwell=[bool]::Parse($parts[7]); TargetOK=[bool]::Parse($parts[8])
        }
    } catch { return $null }
}

function Ensure-Torch {
    param([Parameter(Mandatory=$true)][string]$Python)
    Write-Step 'Checking PyTorch 2.12.1 / CUDA 13.0 / CPU fallback'
    $hasNvidia = Test-NvidiaHardware
    $state = Get-TorchState -Python $Python
    $compatible = $false
    if ($state) {
        $baseVersion = [version]($state.Version.Split('+')[0])
        if ($baseVersion -ge [version]'2.12.1') {
            if ($hasNvidia) {
                $compatible = $state.Available -and $state.TargetOK
            } else {
                $compatible = -not $state.Available
            }
        }
    }
    if (-not $compatible) {
        if ($hasNvidia) {
            Write-Host "NVIDIA hardware detected. Installing PyTorch $torchVersion / CUDA 13.0..."
            & $Python -m pip install --upgrade "torch==$torchVersion" --index-url $cudaIndex | Out-Host
        } else {
            Write-Host "CPU-only system. Installing PyTorch $torchVersion CPU build..."
            & $Python -m pip install --upgrade "torch==$torchVersion" --index-url $cpuIndex | Out-Host
        }
        if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed.' }
        $state = Get-TorchState -Python $Python
    } else {
        Write-Host "Compatible PyTorch already present: $($state.Version). Skipping reinstall."
    }
    if (-not $state) { throw "PyTorch import failed. See $torchDiagnosticPath" }
    if ($hasNvidia -and (-not $state.Available -or -not $state.TargetOK)) {
        throw "NVIDIA hardware is present but CUDA 13/native architecture gate failed: torch=$($state.Version), CUDA=$($state.Cuda), arch=$($state.Architecture), native=$($state.Native)."
    }
    Write-Host "PyTorch OK: $($state.Version) | CUDA $($state.Cuda) | $($state.Gpu) | $($state.Architecture) | native=$($state.Native)"
    Write-BootstrapLog "Torch=$($state.Version); CUDA=$($state.Cuda); GPU=$($state.Gpu); arch=$($state.Architecture); native=$($state.Native)"
}

function Find-FFmpeg {
    Refresh-ProcessPath
    $command = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command ffmpeg -ErrorAction SilentlyContinue }
    if ($command) { return [string]$command.Source }
    if ($env:LOCALAPPDATA) {
        $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\ffmpeg.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return [string]$candidate }
    }
    return $null
}

function Ensure-FFmpeg {
    Write-Step 'Checking FFmpeg'
    $ffmpeg = Find-FFmpeg
    if (-not $ffmpeg) {
        Invoke-WingetInstall -Id 'Gyan.FFmpeg'
        $ffmpeg = Find-FFmpeg
    }
    if (-not $ffmpeg) { throw 'FFmpeg could not be prepared.' }
    $dir = Split-Path -Parent $ffmpeg
    if (@($env:Path -split ';') -notcontains $dir) { $env:Path = "$dir;$env:Path" }
    Write-Host "FFmpeg OK: $ffmpeg"
}

try {
    Write-Host 'Genre_test 0.4.0 portable release bootstrap' -ForegroundColor Green
    Write-BootstrapLog 'Bootstrap started'
    $runtime = Ensure-Python
    $python = Ensure-Venv -Runtime $runtime

    Write-Step 'Preparing pip / NumPy'
    & $python -m pip install --upgrade pip wheel 'setuptools<82' 'numpy>=1.26,<3' | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Python bootstrap package installation failed.' }

    Ensure-Torch -Python $python
    Ensure-FFmpeg

    Write-Step 'Installing/updating Genre_test 0.4.0 dependencies'
    & $python -m pip install -e $repoRoot | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Genre_test dependency installation failed.' }

    $genreExe = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
    $guiExe = Join-Path $repoRoot '.venv\Scripts\genre-test-gui.exe'
    if (-not (Test-Path -LiteralPath $genreExe)) { throw "CLI executable missing: $genreExe" }
    if (-not (Test-Path -LiteralPath $guiExe)) { throw "GUI executable missing: $guiExe" }

    Write-Step 'Release runtime health gate'
    & $genreExe --version | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'genre-test --version failed.' }
    & $genreExe doctor | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'genre-test doctor failed.' }

    Write-Step 'Starting GUI'
    & $guiExe
    exit $LASTEXITCODE
}
catch {
    Write-BootstrapLog "FAIL: $($_.Exception.Message)"
    Write-Host "`n[FAIL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Bootstrap log: $logPath"
    exit 1
}
