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

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @()
    if ($machine) { $parts += $machine }
    if ($user) { $parts += $user }
    if ($parts.Count -gt 0) { $env:Path = ($parts -join ';') }
}

function Get-CompatiblePython {
    Refresh-ProcessPath

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($selector in @('-3.12', '-3.11')) {
            try {
                $v = (& $py.Source $selector -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}|{64 if sys.maxsize > 2**32 else 32}')" 2>$null | Select-Object -Last 1)
                if ($LASTEXITCODE -eq 0 -and $v -match '^3\.(11|12)\|64$') {
                    $version = ($v -split '\|')[0]
                    return [pscustomobject]@{ Exe=$py.Source; Prefix=@($selector); Version=$version; Display="py $selector" }
                }
            } catch {}
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        try {
            $v = (& $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}|{64 if sys.maxsize > 2**32 else 32}')" 2>$null | Select-Object -Last 1)
            if ($LASTEXITCODE -eq 0 -and $v -match '^3\.(11|12)\|64$') {
                $version = ($v -split '\|')[0]
                return [pscustomobject]@{ Exe=$python.Source; Prefix=@(); Version=$version; Display=$python.Source }
            }
        } catch {}
    }
    return $null
}

function Get-WingetPath {
    Refresh-ProcessPath
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { $winget = Get-Command winget -ErrorAction SilentlyContinue }
    if ($winget) { return $winget.Source }

    if ($env:LOCALAPPDATA) {
        $alias = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        if (Test-Path -LiteralPath $alias -PathType Leaf) { return $alias }
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
    ver = tuple(int(''.join(ch for ch in item if ch.isdigit()) or '0') for item in nums)
    ver = ver + (0,) * (3 - len(ver))
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
    ok = ver >= (2, 12, 1) and ((not available) or cuda.startswith('13.0')) and ((not blackwell) or native)
    print(f'__GT_TORCH__|{raw}|{cuda}|{available}|{gpu}|{arch}|{native}|{blackwell}|{ok}')
except Exception as exc:
    print(f'__GT_TORCH_ERROR__|{type(exc).__name__}|{exc}')
    sys.exit(2)
'@

    try {
        $line = (& $Python -c $code 2>$null | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or -not $line -or $line -notlike '__GT_TORCH__|*') { return $null }
        $parts = [string]$line -split '\|'
        return [pscustomobject]@{
            Version=$parts[1]
            Cuda=$parts[2]
            Available=[bool]::Parse($parts[3])
            Gpu=$parts[4]
            Architecture=$parts[5]
            Native=[bool]::Parse($parts[6])
            Blackwell=[bool]::Parse($parts[7])
            TargetOK=[bool]::Parse($parts[8])
        }
    } catch { return $null }
}

$runtime = Get-CompatiblePython
if (-not $runtime -and $InstallPython) {
    $wingetPath = Get-WingetPath
    if (-not $wingetPath -and $IsWindows) {
        $ensureWinget = Join-Path $PSScriptRoot 'ensure_winget.ps1'
        if (Test-Path $ensureWinget) {
            Write-Host 'WinGet not found. Attempting automatic repair...'
            & $ensureWinget
            $wingetPath = Get-WingetPath
        }
    }
    if (-not $wingetPath) { throw 'Python is missing and winget is unavailable.' }
    Write-Host 'Installing Python 3.12 x64...'
    & $wingetPath install --id Python.Python.3.12 --exact --architecture x64 --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 installation failed.' }
    $runtime = Get-CompatiblePython
}
if (-not $runtime) {
    throw 'Compatible Python 3.11/3.12 x64 not found. Run .\scripts\setup.ps1 -InstallPython.'
}
Write-Host "Using Python $($runtime.Version): $($runtime.Display)"

$venvDir = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
if ((Test-Path $venvDir) -and -not (Test-Path $venvPython)) {
    Write-Warning 'Broken .venv detected. Recreating it.'
    Remove-Item -Recurse -Force $venvDir
}
if (-not (Test-Path $venvPython)) {
    Write-Host 'Creating virtual environment...'
    $args = @($runtime.Prefix) + @('-m', 'venv', $venvDir)
    & $runtime.Exe @args
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) { throw 'Virtual environment creation failed.' }
}

& $venvPython -m pip install --upgrade pip wheel 'setuptools<82'
if ($LASTEXITCODE -ne 0) { throw 'pip bootstrap failed.' }
try {
    $cache = (& $venvPython -m pip cache dir 2>$null | Select-Object -Last 1)
    if ($cache) { Write-Host "Shared pip wheel cache: $cache" }
} catch {}

$existing = Get-TorchProbe -Python $venvPython
$hasNvidia = [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)

if ($Cpu) {
    $cpuOK = $existing -and -not $existing.Available -and ([version]($existing.Version.Split('+')[0]) -ge [version]'2.12.1')
    if ($cpuOK) {
        Write-Host "CPU PyTorch already compatible: $($existing.Version). Skipping reinstall."
    } else {
        Write-Host "Installing CPU PyTorch $TorchVersion..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CpuIndex
        if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed.' }
    }
}
elseif ($hasNvidia) {
    if ($existing -and $existing.Available -and $existing.TargetOK) {
        Write-Host "PyTorch already compatible: $($existing.Version), CUDA $($existing.Cuda), $($existing.Architecture), native=$($existing.Native)."
        Write-Host 'Skipping the multi-GB PyTorch reinstall.'
    } else {
        Write-Host "Installing PyTorch $TorchVersion / CUDA 13.0..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CudaIndex
        if ($LASTEXITCODE -ne 0) { throw 'CUDA 13.0 PyTorch installation failed.' }
    }
}
else {
    if ($existing -and ([version]($existing.Version.Split('+')[0]) -ge [version]'2.12.1')) {
        Write-Host "PyTorch already compatible: $($existing.Version). Skipping reinstall."
    } else {
        Write-Host "NVIDIA GPU not detected. Installing CPU PyTorch $TorchVersion..."
        & $venvPython -m pip install --upgrade "torch==$TorchVersion" --index-url $CpuIndex
        if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed.' }
    }
}

$probe = Get-TorchProbe -Python $venvPython
if (-not $probe) { throw 'PyTorch cannot be imported after installation.' }
if ($hasNvidia -and -not $Cpu -and -not $probe.TargetOK) {
    throw "GPU runtime target failed: torch=$($probe.Version), CUDA=$($probe.Cuda), arch=$($probe.Architecture), native=$($probe.Native)."
}
Write-Host "PyTorch: $($probe.Version) | CUDA $($probe.Cuda) | $($probe.Gpu) | $($probe.Architecture) | native=$($probe.Native)"

& $venvPython -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Genre_test dependency installation failed.' }

if (-not $SkipFFmpeg) {
    Write-Host "`nChecking FFmpeg..."
    $ensureFFmpeg = Join-Path $PSScriptRoot 'ensure_ffmpeg.ps1'
    if ($IsWindows) { & $ensureFFmpeg -Required } else { & $ensureFFmpeg }
} else {
    Write-Warning 'FFmpeg bootstrap skipped by -SkipFFmpeg.'
}

$genreExe = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
if (-not (Test-Path $genreExe)) { throw "CLI executable missing: $genreExe" }
Write-Host "`nRuntime check:"
& $genreExe doctor
if ($LASTEXITCODE -ne 0) { throw 'genre-test doctor failed.' }

Write-Host "`nSetup complete: PyTorch >=2.12.1 / CUDA 13.0 / native Blackwell when applicable."
Write-Host "GUI: .\scripts\gui.ps1"
