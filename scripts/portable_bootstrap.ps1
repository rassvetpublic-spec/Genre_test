# Windows PowerShell 5.1 compatible one-click bootstrap for Genre_test 0.3.6 portable.
[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$expectedRoot = 'C:\Genre_test_0.3.6_portable'
Set-Location $repoRoot
$stateDir = Join-Path $repoRoot '.genre_test'
$logPath = Join-Path $stateDir 'bootstrap.log'
$torchStdoutPath = Join-Path $stateDir 'torch_probe_stdout.txt'
$torchDiagnosticPath = Join-Path $stateDir 'torch_import_diagnostic.txt'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Write-BootstrapLog {
    param([Parameter(Mandatory=$true)][string]$Message)
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "[$timestamp] $Message"
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
    if ($command) { return $command.Source }
    if ($env:LOCALAPPDATA) {
        $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

function Require-Winget {
    $winget = Find-Winget
    if ($winget) { return $winget }
    Write-Host ''
    Write-Host '[FAIL] Windows Package Manager (winget) is missing.' -ForegroundColor Red
    Write-Host 'Automatic WinGet repair already ran but winget is still unavailable.'
    Write-Host 'Install/update App Installer from Microsoft Store and run Genre_test_START.cmd again.'
    try { Start-Process 'ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1' | Out-Null } catch {}
    throw 'winget is required because a missing component must be installed.'
}

function Invoke-WingetInstall {
    param(
        [Parameter(Mandatory=$true)][string]$Id,
        [switch]$UserScope
    )
    $winget = Require-Winget
    $arguments = @(
        'install', '--id', $Id, '--exact', '--source', 'winget',
        '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'
    )
    if ($UserScope) { $arguments += @('--scope', 'user') }
    Write-BootstrapLog "winget $($arguments -join ' ')"
    & $winget @arguments
    $code = $LASTEXITCODE
    if ($code -ne 0 -and $code -ne 3010) {
        throw "winget failed to install $Id (exit code $code)."
    }
    Refresh-ProcessPath
}

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [string[]]$PrefixArgs = @()
    )
    try {
        $pythonCode = "import sys,struct; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'|'+str(struct.calcsize('P')*8))"
        $invokeArgs = @($PrefixArgs) + @('-c', $pythonCode)
        $text = (& $Exe @invokeArgs 2>$null | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or -not $text) { return $null }
        $pieces = [string]$text -split '\|'
        if ($pieces.Count -ne 2) { return $null }
        $version = [version]$pieces[0]
        $bits = [int]$pieces[1]
        if ($version.Major -eq 3 -and $version.Minor -ge 11 -and $version.Minor -lt 13 -and $bits -eq 64) {
            return [pscustomobject]@{
                Exe = $Exe
                PrefixArgs = @($PrefixArgs)
                Version = $version
                Bits = $bits
                Display = if ($PrefixArgs.Count -gt 0) { "$Exe $($PrefixArgs -join ' ')" } else { $Exe }
            }
        }
    } catch {}
    return $null
}

function Find-CompatiblePython {
    Refresh-ProcessPath
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if ($py) {
        foreach ($selector in @('-3.12', '-3.11')) {
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

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python311\python.exe')
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            $found = Test-PythonCandidate -Exe $candidate
            if ($found) { return $found }
        }
    }
    return $null
}

function Ensure-Python {
    Write-Step 'Checking Python 3.11/3.12 x64'
    $runtime = Find-CompatiblePython
    if (-not $runtime) {
        Write-Host 'Compatible Python was not found. Installing Python 3.12 x64 with winget...'
        Invoke-WingetInstall -Id 'Python.Python.3.12' -UserScope
        Start-Sleep -Seconds 1
        $runtime = Find-CompatiblePython
    }
    if (-not $runtime) {
        throw 'Python 3.12 installation completed but a compatible x64 python.exe could not be located.'
    }
    Write-Host "Python OK: $($runtime.Version) x64"
    Write-BootstrapLog "Python=$($runtime.Display); version=$($runtime.Version); bits=$($runtime.Bits)"
    return $runtime
}

function Ensure-Venv {
    param([Parameter(Mandatory=$true)]$Runtime)
    $venvDir = Join-Path $repoRoot '.venv'
    $venvPython = Join-Path $venvDir 'Scripts\python.exe'

    if (Test-Path -LiteralPath $venvPython) {
        $valid = Test-PythonCandidate -Exe $venvPython
        if (-not $valid) {
            Write-Host 'Existing .venv is invalid. Recreating...'
            Remove-Item -LiteralPath $venvDir -Recurse -Force
        }
    } elseif (Test-Path -LiteralPath $venvDir) {
        Write-Host 'Incomplete .venv detected. Recreating...'
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Step 'Creating private virtual environment (.venv)'
        $invokeArgs = @($Runtime.PrefixArgs) + @('-m', 'venv', $venvDir)
        & $Runtime.Exe @invokeArgs
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) {
            throw 'Virtual environment creation failed.'
        }
    } else {
        Write-Host '.venv OK'
    }
    return $venvPython
}

function Ensure-PythonBootstrapPackages {
    param([Parameter(Mandatory=$true)][string]$Python)
    Write-Step 'Preparing Python runtime packages'
    & $Python -m pip install --upgrade pip wheel 'setuptools<82' 'numpy>=1.26,<3'
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to prepare pip/wheel/setuptools/NumPy.'
    }
    $numpyVersion = (& $Python -c "import numpy; print(numpy.__version__)" 2>$null | Select-Object -Last 1)
    if ($LASTEXITCODE -ne 0 -or -not $numpyVersion) {
        throw 'NumPy cannot be imported after installation.'
    }
    Write-Host "NumPy OK: $numpyVersion"
    Write-BootstrapLog "NumPy=$numpyVersion"
}

function Test-NvidiaGpu {
    $nvidia = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if (-not $nvidia) { $nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue }
    if ($nvidia) { return $true }
    $candidate = Join-Path $env:WINDIR 'System32\nvidia-smi.exe'
    return (Test-Path -LiteralPath $candidate -PathType Leaf)
}

function Get-TorchState {
    param([Parameter(Mandatory=$true)][string]$Python)

    Remove-Item -LiteralPath $torchStdoutPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $torchDiagnosticPath -Force -ErrorAction SilentlyContinue

    $marker = '__GENRE_TEST_TORCH_OK__'
    $probeCode = "import torch; print('$marker|'+str(torch.__version__)+'|'+str(torch.version.cuda or 'none')+'|'+str(bool(torch.cuda.is_available())))"

    try {
        & $Python -c $probeCode 1> $torchStdoutPath 2> $torchDiagnosticPath
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = 1
        Add-Content -LiteralPath $torchDiagnosticPath -Encoding UTF8 -Value $_.Exception.ToString()
    }

    $stdoutLines = @()
    if (Test-Path -LiteralPath $torchStdoutPath) {
        $stdoutLines = @(Get-Content -LiteralPath $torchStdoutPath -ErrorAction SilentlyContinue)
    }
    $markerLine = $stdoutLines | Where-Object { $_ -like "$marker|*" } | Select-Object -Last 1

    if ($exitCode -eq 0 -and $markerLine) {
        $state = [string]$markerLine
        $state = $state.Substring($marker.Length + 1)
        if (Test-Path -LiteralPath $torchDiagnosticPath) {
            $warningText = (Get-Content -LiteralPath $torchDiagnosticPath -Raw -ErrorAction SilentlyContinue)
            if ($warningText) {
                Write-BootstrapLog "PyTorch probe warnings: $($warningText.Trim())"
            }
        }
        return $state
    }

    if (Test-Path -LiteralPath $torchDiagnosticPath) {
        $diagnostic = Get-Content -LiteralPath $torchDiagnosticPath -Raw -ErrorAction SilentlyContinue
        if ($diagnostic) { Write-BootstrapLog "PyTorch import failure: $($diagnostic.Trim())" }
    }
    return $null
}

function Ensure-Torch {
    param([Parameter(Mandatory=$true)][string]$Python)
    Write-Step 'Checking PyTorch / GPU backend'
    $hasNvidia = Test-NvidiaGpu
    $state = Get-TorchState -Python $Python
    $needsInstall = -not $state

    if ($hasNvidia -and $state -and ($state -notmatch '\|12\.8\|')) {
        $needsInstall = $true
    }

    if ($needsInstall) {
        if ($hasNvidia) {
            Write-Host 'NVIDIA GPU detected. Installing PyTorch CUDA 12.8 build...'
            & $Python -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
        } else {
            Write-Host 'NVIDIA GPU not detected. Installing CPU PyTorch build...'
            & $Python -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cpu
        }
        if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed.' }
        $state = Get-TorchState -Python $Python
    }

    if (-not $state) {
        throw "PyTorch import failed. See $torchDiagnosticPath"
    }

    Write-Host "PyTorch OK: $state"
    Write-BootstrapLog "Torch=$state; nvidia_detected=$hasNvidia"
}

function Find-FFmpeg {
    Refresh-ProcessPath
    $command = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command ffmpeg -ErrorAction SilentlyContinue }
    if ($command) { return $command.Source }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\ffmpeg.exe'),
        (Join-Path $env:USERPROFILE 'scoop\shims\ffmpeg.exe'),
        (Join-Path $env:ProgramData 'chocolatey\bin\ffmpeg.exe'),
        (Join-Path $env:ProgramFiles 'ffmpeg\bin\ffmpeg.exe')
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $candidate }
    }
    return $null
}

function Ensure-FFmpeg {
    Write-Step 'Checking FFmpeg'
    $ffmpeg = Find-FFmpeg
    if (-not $ffmpeg) {
        Write-Host 'FFmpeg was not found. Installing Gyan.FFmpeg with winget...'
        Invoke-WingetInstall -Id 'Gyan.FFmpeg'
        Start-Sleep -Milliseconds 700
        $ffmpeg = Find-FFmpeg
    }
    if (-not $ffmpeg) { throw 'FFmpeg installation finished but ffmpeg.exe could not be located.' }
    $dir = Split-Path -Parent $ffmpeg
    if (@($env:Path -split ';') -notcontains $dir) { $env:Path = "$dir;$env:Path" }
    $versionLine = (& $ffmpeg -version 2>$null | Select-Object -First 1)
    Write-Host "FFmpeg OK: $ffmpeg"
    if ($versionLine) { Write-Host $versionLine }
    Write-BootstrapLog "FFmpeg=$ffmpeg"
}

function Install-GenreTest {
    param([Parameter(Mandatory=$true)][string]$Python)
    Write-Step 'Checking Genre_test 0.3.6 and Python dependencies'
    $genreExe = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
    $needsInstall = $true
    if (Test-Path -LiteralPath $genreExe) {
        try {
            $versionText = (& $genreExe --version 2>$null | Select-Object -Last 1)
            if ($LASTEXITCODE -eq 0 -and $versionText -match '0\.3\.6') { $needsInstall = $false }
        } catch {}
    }

    if ($needsInstall) {
        Write-Host 'Installing Genre_test runtime dependencies...'
        & $Python -m pip install -e $repoRoot
        if ($LASTEXITCODE -ne 0) { throw 'Genre_test dependency installation failed.' }
    } else {
        Write-Host 'Genre_test 0.3.6 package OK'
    }

    $healthCode = "from genre_test.runtime_health import collect_runtime_health; h=collect_runtime_health(); print('Runtime Health: '+h.overall_status+' | '+h.compact_summary); raise SystemExit(1 if h.overall_status == 'FAIL' else 0)"
    & $Python -c $healthCode
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Runtime dependency check failed. Repairing package dependencies...' -ForegroundColor Yellow
        & $Python -m pip install --upgrade -e $repoRoot
        if ($LASTEXITCODE -ne 0) { throw 'Dependency repair failed.' }
        & $Python -c $healthCode
        if ($LASTEXITCODE -ne 0) { throw 'Runtime Health still reports FAIL after repair.' }
    }
    return $genreExe
}

function Run-Diagnostics {
    param([Parameter(Mandatory=$true)][string]$GenreExe)
    Write-Step 'Runtime diagnostics'
    & $GenreExe --version
    if ($LASTEXITCODE -ne 0) { throw 'genre-test --version failed.' }
    & $GenreExe doctor
    if ($LASTEXITCODE -ne 0) { throw 'genre-test doctor failed.' }
    Write-BootstrapLog 'Diagnostics PASS'
}

try {
    Write-BootstrapLog '============================================================'
    Write-BootstrapLog 'Portable startup begin'
    Write-Host 'Package: Genre_test 0.3.6 Portable'
    Write-Host "Folder : $repoRoot"
    Write-Host "Log    : $logPath"

    if (-not [Environment]::Is64BitOperatingSystem) {
        throw '64-bit Windows is required.'
    }

    if (-not [string]::Equals($repoRoot.TrimEnd('\'), $expectedRoot.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Wrong installation folder. Extract the ZIP so the package is exactly at $expectedRoot"
    }

    $drive = Get-PSDrive -Name C -ErrorAction SilentlyContinue
    if ($drive -and $drive.Free -lt 8GB) {
        Write-Host '[WARN] Less than 8 GB free space is available. First setup/model download may fail.' -ForegroundColor Yellow
    }

    $runtime = Ensure-Python
    $venvPython = Ensure-Venv -Runtime $runtime
    Ensure-PythonBootstrapPackages -Python $venvPython
    Ensure-Torch -Python $venvPython
    Ensure-FFmpeg
    $genreExe = Install-GenreTest -Python $venvPython
    Run-Diagnostics -GenreExe $genreExe

    $guiExe = Join-Path $repoRoot '.venv\Scripts\genre-test-gui.exe'
    if (-not (Test-Path -LiteralPath $guiExe)) {
        throw "GUI executable is missing: $guiExe"
    }

    Write-Step 'Starting Genre_test GUI'
    Write-Host 'First analysis may download the pinned MAEST model. This is normal.'
    Write-BootstrapLog "Launching GUI=$guiExe"
    Start-Process -FilePath $guiExe -WorkingDirectory $repoRoot
    Write-BootstrapLog 'Portable startup complete'
    exit 0
}
catch {
    $message = $_.Exception.Message
    Write-Host "`n[FAIL] $message" -ForegroundColor Red
    Write-BootstrapLog "FAIL: $message"
    Write-BootstrapLog $_.ScriptStackTrace
    exit 1
}
