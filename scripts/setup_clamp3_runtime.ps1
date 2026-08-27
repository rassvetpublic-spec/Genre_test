param(
    [string]$RepoRoot = "",
    [switch]$Install,
    [switch]$DownloadModels,
    [switch]$AcceptMertNonCommercialTerms,
    [switch]$RunSmoke,
    [switch]$RunSidecarSmoke,
    [string]$AudioPath = "",
    [string]$TextQuery = "мрачный электронный трек с мощными барабанами и напряжённой энергией",
    [int]$Repeat = 2
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ClampRevision = "9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8"
$MertLicense = "CC-BY-NC-4.0"
$TorchVersion = "2.12.1"
$TorchIndex = "https://download.pytorch.org/whl/cu130"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$RepoRoot = (Resolve-Path $RepoRoot).Path
$RuntimeRoot = Join-Path $RepoRoot ".genre_test\retrieval"
$RuntimeDir = Join-Path $RuntimeRoot "runtime"
$VenvDir = Join-Path $RuntimeDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$CorePythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$UpstreamDir = Join-Path $RuntimeRoot "upstream\clamp3"
$LogDir = Join-Path $RepoRoot ".genre_test\logs"
$SmokeScript = Join-Path $RepoRoot "scripts\clamp3_runtime_smoke.py"
$SidecarClientSmokeScript = Join-Path $RepoRoot "scripts\clamp3_sidecar_client_smoke.py"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$ArgumentList
    )
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($ArgumentList -join ' ')"
    }
}

function Get-Python312 {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @($py.Source, "-3.12")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @($python.Source)
        }
    }

    throw "Python 3.12 x64 is required for the first CLaMP 3 sidecar spike."
}

Write-Section "Genre_test CLaMP 3 P0 runtime"
Write-Host "Repo root    : $RepoRoot"
Write-Host "Runtime root : $RuntimeRoot"
Write-Host "Log root     : $LogDir"
Write-Host "CLaMP code   : $ClampRevision"
Write-Host "Torch target : $TorchVersion / cu130"

if (-not ($Install -or $DownloadModels -or $RunSmoke -or $RunSidecarSmoke)) {
    Write-Host ""
    Write-Host "No mutation requested. Current state:"
    Write-Host "  venv       : $(Test-Path $PythonExe)"
    Write-Host "  upstream   : $(Test-Path (Join-Path $UpstreamDir '.git'))"
    Write-Host "  models dir : $(Test-Path (Join-Path $RuntimeRoot 'models'))"
    Write-Host ""
    Write-Host "Use -Install to create the isolated runtime."
    Write-Host "Use -DownloadModels -AcceptMertNonCommercialTerms for explicit model download."
    Write-Host "Use -RunSmoke [-AudioPath <WAV>] for direct isolated-runtime inference."
    Write-Host "Use -RunSidecarSmoke [-AudioPath <WAV>] for core -> persistent sidecar integration."
    return
}

if ($DownloadModels -and -not $AcceptMertNonCommercialTerms) {
    throw "Model download includes MERT ($MertLicense). Re-run with -AcceptMertNonCommercialTerms after reviewing the non-commercial license gate."
}

if ($Install) {
    Write-Section "Create isolated Python 3.12 runtime"
    New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
    # Force a clean array boundary: native probe stdout must never become launcher arguments.
    $python312 = @(Get-Python312)
    if (-not (Test-Path $PythonExe)) {
        $launcher = $python312[0]
        $launcherArgs = @()
        if ($python312.Count -gt 1) {
            $launcherArgs += $python312[1..($python312.Count - 1)]
        }
        $launcherArgs += @("-m", "venv", $VenvDir)
        Invoke-Checked $launcher @launcherArgs
    }

    Invoke-Checked $PythonExe -m pip install --upgrade pip
    Invoke-Checked $PythonExe -m pip install --index-url $TorchIndex "torch==$TorchVersion"
    Invoke-Checked $PythonExe -m pip install `
        "transformers==4.40.0" `
        "accelerate==0.34.0" `
        "numpy==1.26.4" `
        "huggingface_hub==0.24.7" `
        "nnAudio==0.3.3" `
        "tqdm==4.66.5" `
        "unidecode==1.3.6" `
        "soundfile==0.12.1" `
        "scipy==1.13.1" `
        "sentencepiece==0.2.0" `
        "safetensors>=0.4.3,<1"

    Write-Section "Pin upstream CLaMP source"
    New-Item -ItemType Directory -Force -Path (Split-Path $UpstreamDir -Parent) | Out-Null
    if (-not (Test-Path (Join-Path $UpstreamDir ".git"))) {
        Invoke-Checked git clone --filter=blob:none --no-checkout https://github.com/sanderwood/clamp3.git $UpstreamDir
    }
    Invoke-Checked git -C $UpstreamDir fetch --depth 1 origin $ClampRevision
    Invoke-Checked git -C $UpstreamDir checkout --detach $ClampRevision
    $actualRevision = (& git -C $UpstreamDir rev-parse HEAD).Trim()
    if ($actualRevision -ne $ClampRevision) {
        throw "Pinned upstream checkout mismatch: expected $ClampRevision, got $actualRevision"
    }
}

if (-not (Test-Path $PythonExe)) {
    throw "Isolated runtime is missing. Run this script with -Install first."
}
if (-not (Test-Path (Join-Path $UpstreamDir ".git"))) {
    throw "Pinned CLaMP source checkout is missing. Run this script with -Install first."
}

Write-Section "Runtime doctor"
Write-Host "MERT terms   : $MertLicense (recorded provenance; development setup prompt deferred)"
Invoke-Checked $PythonExe -c "import sys, torch; print('python', sys.version.split()[0]); print('torch', torch.__version__); print('cuda_runtime', torch.version.cuda); print('cuda_available', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'); print('arch_list', torch.cuda.get_arch_list() if torch.cuda.is_available() else [])"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ($DownloadModels) {
    Write-Section "Explicit pinned model download"
    Write-Host "Downloading CLaMP 3 SAAS + XLM-R + MERT. This can use several GB of disk/cache."
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $downloadProbe = Join-Path $LogDir "clamp3_download_probe_$stamp.json"
    $downloadArgs = @(
        $SmokeScript,
        "--runtime-root", $RuntimeRoot,
        "--download-models",
        "--text", $TextQuery,
        "--repeat", "1",
        "--json-out", $downloadProbe
    )
    if (-not [string]::IsNullOrWhiteSpace($AudioPath)) {
        if (-not (Test-Path $AudioPath)) {
            throw "AudioPath does not exist: $AudioPath"
        }
        $downloadArgs += @("--audio", (Resolve-Path $AudioPath).Path)
    }
    Invoke-Checked $PythonExe @downloadArgs
    Write-Host "Log: $downloadProbe" -ForegroundColor Green
}

if ($RunSmoke) {
    Write-Section "Real direct-runtime embedding smoke"
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $evidencePath = Join-Path $LogDir "clamp3_runtime_smoke_$stamp.json"
    $args = @(
        $SmokeScript,
        "--runtime-root", $RuntimeRoot,
        "--text", $TextQuery,
        "--repeat", [string]$Repeat,
        "--json-out", $evidencePath
    )
    if (-not [string]::IsNullOrWhiteSpace($AudioPath)) {
        if (-not (Test-Path $AudioPath)) {
            throw "AudioPath does not exist: $AudioPath"
        }
        $args += @("--audio", (Resolve-Path $AudioPath).Path)
    }
    Invoke-Checked $PythonExe @args
    Write-Host "Log: $evidencePath" -ForegroundColor Green
}

if ($RunSidecarSmoke) {
    Write-Section "Core -> persistent CLaMP sidecar smoke"
    if (-not (Test-Path $CorePythonExe)) {
        throw "Core Genre_test Python is missing: $CorePythonExe"
    }
    if (-not (Test-Path $SidecarClientSmokeScript)) {
        throw "Sidecar client smoke script is missing: $SidecarClientSmokeScript"
    }
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $sidecarEvidencePath = Join-Path $LogDir "clamp3_sidecar_smoke_$stamp.json"
    $sidecarArgs = @(
        $SidecarClientSmokeScript,
        "--repo-root", $RepoRoot,
        "--text", $TextQuery,
        "--repeat", [string]$Repeat,
        "--timeout", "300",
        "--json-out", $sidecarEvidencePath
    )
    if (-not [string]::IsNullOrWhiteSpace($AudioPath)) {
        if (-not (Test-Path $AudioPath)) {
            throw "AudioPath does not exist: $AudioPath"
        }
        $sidecarArgs += @("--audio", (Resolve-Path $AudioPath).Path)
    }
    Invoke-Checked $CorePythonExe @sidecarArgs
    Write-Host "Log: $sidecarEvidencePath" -ForegroundColor Green
}

Write-Section "Done"
Write-Host "Core .venv was not modified. Retrieval runtime remains isolated under .genre_test\retrieval."
Write-Host "All CLaMP diagnostics are stored under .genre_test\logs."
