[CmdletBinding()]
param(
    [switch]$InstallDevDependencies,
    [switch]$SkipFullTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$LogDir = Join-Path $RepoRoot '.genre_test\logs'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportPath = Join-Path $LogDir "retrieval_p0_local_$Stamp.json"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Steps = @()
$OverallPass = $true
$StartedAt = Get-Date

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $started = Get-Date
    try {
        & $Action | Out-Host
        $elapsed = (Get-Date) - $started
        $script:Steps += [ordered]@{
            name = $Name
            status = 'PASS'
            seconds = [math]::Round($elapsed.TotalSeconds, 3)
        }
        return $true
    }
    catch {
        $elapsed = (Get-Date) - $started
        $script:Steps += [ordered]@{
            name = $Name
            status = 'FAIL'
            seconds = [math]::Round($elapsed.TotalSeconds, 3)
            error = $_.Exception.Message
        }
        Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Genre_test virtual environment was not found: $Python. Run .\Genre_test_START.cmd once first."
}

$GitCommit = (& git -C $RepoRoot rev-parse HEAD).Trim()
$GitBranch = (& git -C $RepoRoot branch --show-current).Trim()
$PythonVersion = (& $Python --version 2>&1).ToString().Trim()

$GpuInfo = $null
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    try {
        $GpuLine = & nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits 2>$null |
            Select-Object -First 1
        if ($GpuLine) {
            $GpuInfo = $GpuLine.Trim()
        }
    }
    catch {
        $GpuInfo = $null
    }
}

if ($InstallDevDependencies) {
    if (-not (Invoke-Step 'Install/update local dev dependencies' {
        & $Python -m pip install -e "${RepoRoot}[dev]"
        if ($LASTEXITCODE -ne 0) { throw "pip install failed with exit code $LASTEXITCODE" }
    })) {
        $OverallPass = $false
    }
}

if (-not (Invoke-Step 'Python compileall' {
    & $Python -m compileall -q (Join-Path $RepoRoot 'src') (Join-Path $RepoRoot 'tests')
    if ($LASTEXITCODE -ne 0) { throw "compileall failed with exit code $LASTEXITCODE" }
})) {
    $OverallPass = $false
}

if (-not (Invoke-Step 'Ruff' {
    & $Python -m ruff check (Join-Path $RepoRoot 'src') (Join-Path $RepoRoot 'tests')
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed with exit code $LASTEXITCODE" }
})) {
    $OverallPass = $false
}

if (-not (Invoke-Step 'Retrieval P0 regression tests' {
    $TestFiles = @(
        (Join-Path $RepoRoot 'tests\test_retrieval_foundation.py'),
        (Join-Path $RepoRoot 'tests\test_retrieval_store.py'),
        (Join-Path $RepoRoot 'tests\test_clamp3_sidecar_backend.py'),
        (Join-Path $RepoRoot 'tests\test_clamp3_p0_gate.py')
    )
    & $Python -m pytest -q @TestFiles
    if ($LASTEXITCODE -ne 0) { throw "retrieval pytest failed with exit code $LASTEXITCODE" }
})) {
    $OverallPass = $false
}

if (-not $SkipFullTests) {
    if (-not (Invoke-Step 'Full pytest suite' {
        & $Python -m pytest -q (Join-Path $RepoRoot 'tests')
        if ($LASTEXITCODE -ne 0) { throw "full pytest failed with exit code $LASTEXITCODE" }
    })) {
        $OverallPass = $false
    }
}

if (-not (Invoke-Step 'Optional CLaMP runtime health probe' {
    & $Python (Join-Path $RepoRoot 'scripts\clamp3_runtime_probe.py')
    if ($LASTEXITCODE -ne 0) { throw "runtime probe failed with exit code $LASTEXITCODE" }
})) {
    $OverallPass = $false
}

if (-not (Invoke-Step 'Flat runtime-state layout' {
    $Legacy = Join-Path $RepoRoot '.genre_test\retrieval'
    if (Test-Path -LiteralPath $Legacy) {
        throw "obsolete state directory still exists: $Legacy"
    }
    $Expected = @(
        (Join-Path $RepoRoot '.genre_test\logs'),
        (Join-Path $RepoRoot '.genre_test\models'),
        (Join-Path $RepoRoot '.genre_test\runtimes\clamp3'),
        (Join-Path $RepoRoot '.genre_test\upstream\clamp3')
    )
    foreach ($Path in $Expected) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "expected state path is missing: $Path"
        }
    }
})) {
    $OverallPass = $false
}

if (-not (Invoke-Step 'Retrieval SQLite/cache/index smoke' {
    $Smoke = @'
from pathlib import Path
from tempfile import TemporaryDirectory

from genre_test.retrieval import (
    DenseCosineIndex,
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalStore,
)

backend = RetrievalBackendInfo(
    backend_name="local-smoke",
    backend_version="1",
    clamp_code_revision="smoke",
    clamp_weight_name="smoke.pth",
    clamp_weight_sha256="a" * 64,
    mert_model_id="smoke-mert",
    mert_revision="smoke",
    text_model_id="smoke-text",
    text_model_revision="smoke",
    text_tokenizer_revision="smoke",
    preprocessing_version="smoke-v1",
    embedding_dim=3,
)

with TemporaryDirectory() as td:
    store = RetrievalStore(Path(td) / "retrieval.sqlite3")
    for track_id, values in (
        ("track-a", (1.0, 0.0, 0.0)),
        ("track-b", (0.8, 0.2, 0.0)),
        ("track-c", (0.0, 1.0, 0.0)),
    ):
        identity = EmbeddingIdentity(
            backend_fingerprint=backend.fingerprint,
            scope="full",
            track_id=track_id,
        )
        vector = EmbeddingVector.normalized(identity, values, expected_dim=3)
        store.put(vector, backend=backend, path=f"{track_id}.wav")

    index = DenseCosineIndex.from_store(store, backend_fingerprint=backend.fingerprint)
    query_identity = EmbeddingIdentity.for_text(
        backend.fingerprint,
        "энергичный трек",
        language="ru",
    )
    query = EmbeddingVector.normalized(query_identity, (1.0, 0.0, 0.0), expected_dim=3)
    hits = index.search(query, top_k=2)
    assert [hit.track_id for hit in hits] == ["track-a", "track-b"]
    assert store.stats(backend_fingerprint=backend.fingerprint)["total"] == 3

print("LOCAL_RETRIEVAL_SMOKE_PASS")
'@

    $Smoke | & $Python -
    if ($LASTEXITCODE -ne 0) { throw "retrieval smoke failed with exit code $LASTEXITCODE" }
})) {
    $OverallPass = $false
}

$FinishedAt = Get-Date
$Clamp3Python = [Environment]::GetEnvironmentVariable('GENRE_TEST_CLAMP3_PYTHON')
$Report = [ordered]@{
    schema_version = 1
    status = if ($OverallPass) { 'PASS' } else { 'FAIL' }
    started_at = $StartedAt.ToString('o')
    finished_at = $FinishedAt.ToString('o')
    elapsed_seconds = [math]::Round(($FinishedAt - $StartedAt).TotalSeconds, 3)
    repository = $RepoRoot
    git_branch = $GitBranch
    git_commit = $GitCommit
    powershell = $PSVersionTable.PSVersion.ToString()
    python = $PythonVersion
    gpu = $GpuInfo
    clamp3_python = $Clamp3Python
    log_dir = $LogDir
    steps = $Steps
}

$Report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding utf8

$ResultColor = if ($OverallPass) { 'Green' } else { 'Red' }
Write-Host "`n=== LOCAL RETRIEVAL P0 GATE: $($Report.status) ===" -ForegroundColor $ResultColor
Write-Host "Report: $ReportPath"
Write-Host "Commit: $GitCommit"
Write-Host "GPU: $(if ($GpuInfo) { $GpuInfo } else { 'N/A' })"

if (-not $OverallPass) {
    exit 1
}
