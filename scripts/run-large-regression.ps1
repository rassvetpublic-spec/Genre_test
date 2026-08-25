#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Source,
    [ValidateSet('auto','fast','accurate')][string]$Mode = 'auto',
    [switch]$FullValidation,
    [switch]$SkipBatch
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

$genre = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
if (-not (Test-Path -LiteralPath $genre -PathType Leaf)) {
    throw 'Genre_test environment is missing. Run .\Genre_test_START.cmd once before regression.'
}
if (-not (Test-Path -LiteralPath $Source)) {
    throw "Regression source does not exist: $Source"
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$sessionRoot = Join-Path $repoRoot "results\large_regression\$stamp"
$batchOut = Join-Path $sessionRoot 'batch'
$validationOut = Join-Path $sessionRoot 'validation'
$logPath = Join-Path $sessionRoot 'run.log'
New-Item -ItemType Directory -Force -Path $sessionRoot | Out-Null

Start-Transcript -LiteralPath $logPath -Force | Out-Null
try {
    Write-Host "Genre_test large regression" -ForegroundColor Cyan
    Write-Host "Source: $Source"
    Write-Host "Mode: $Mode"
    Write-Host "Output: $sessionRoot"

    Write-Host "`n== Runtime gate ==" -ForegroundColor Cyan
    & $genre --version
    if ($LASTEXITCODE -ne 0) { throw 'genre-test --version failed.' }
    & $genre doctor
    if ($LASTEXITCODE -ne 0) { throw 'genre-test doctor failed.' }

    # Validation intentionally runs before the ordinary batch. The batch persists fresh
    # history, so reversing this order would hide results that were stale/missing at
    # the start of the regression session.
    if ($FullValidation) {
        Write-Host "`n== Full mode-convergence validation ==" -ForegroundColor Cyan
        & $genre validate $Source --out $validationOut --device auto --compare-modes --filter all
        if ($LASTEXITCODE -ne 0) { throw 'Full Validation failed.' }
    } else {
        Write-Host "`n== Pre-batch stale/missing history recheck ==" -ForegroundColor Cyan
        & $genre validate $Source --out $validationOut --device auto --mode $Mode --filter old_versions
        if ($LASTEXITCODE -ne 0) { throw 'Validation recheck failed.' }
    }

    if (-not $SkipBatch) {
        Write-Host "`n== Ensemble batch ==" -ForegroundColor Cyan
        & $genre batch $Source --out $batchOut --device auto --mode $Mode --semantic auto --view all --full-path
        if ($LASTEXITCODE -ne 0) { throw 'Large ensemble batch failed.' }
    }

    Write-Host "`nLarge regression complete." -ForegroundColor Green
    Write-Host "Session: $sessionRoot"
    Write-Host "Transcript: $logPath"
}
finally {
    Stop-Transcript | Out-Null
}
