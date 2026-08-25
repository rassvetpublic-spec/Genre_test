#requires -Version 7.0
[CmdletBinding()]
param(
    [string[]]$Source = @('C:\GIT\SUNO'),
    [ValidateSet('auto', 'fast', 'accurate')]
    [string]$Mode = 'auto',
    [ValidateSet('all', 'old_versions', 'unstable')]
    [string]$ValidationFilter = 'all',
    [switch]$CompareModes,
    [switch]$SkipBatch,
    [switch]$SkipValidation,
    [switch]$NoHistory
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

$genreTest = Join-Path $repoRoot '.venv\Scripts\genre-test.exe'
if (-not (Test-Path -LiteralPath $genreTest -PathType Leaf)) {
    throw "Genre_test runtime is not prepared: $genreTest. Run .\Genre_test_START.cmd once first."
}

$resolvedSources = [System.Collections.Generic.List[string]]::new()
foreach ($item in $Source) {
    if (-not (Test-Path -LiteralPath $item)) {
        throw "Regression source does not exist: $item"
    }
    $resolvedSources.Add((Resolve-Path -LiteralPath $item).Path)
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runRoot = Join-Path $repoRoot "results\large_regression\$stamp"
$batchRoot = Join-Path $runRoot 'batch'
$validationRoot = Join-Path $runRoot 'validation'
New-Item -ItemType Directory -Force -Path $runRoot, $batchRoot, $validationRoot | Out-Null

$transcript = Join-Path $runRoot 'large_regression.log'
$started = Get-Date
$commit = (& git -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1)
$version = (& $genreTest --version 2>$null | Select-Object -Last 1)
$protectValidationFilter = -not $SkipValidation -and $ValidationFilter -ne 'all'
$batchNoHistory = [bool]$NoHistory -or $protectValidationFilter

@(
    "Started: $($started.ToString('o'))"
    "Repository: $repoRoot"
    "Git commit: $commit"
    "Version: $version"
    "Mode: $Mode"
    "CompareModes: $CompareModes"
    "ValidationFilter: $ValidationFilter"
    "BatchNoHistory: $batchNoHistory"
    'Sources:'
    ($resolvedSources | ForEach-Object { "  $_" })
) | Set-Content -LiteralPath (Join-Path $runRoot 'RUN_INFO.txt') -Encoding UTF8

Start-Transcript -LiteralPath $transcript -Force | Out-Null
try {
    Write-Host '============================================================'
    Write-Host ' Genre_test large regression'
    Write-Host '============================================================'
    Write-Host "Output: $runRoot"
    Write-Host "Commit: $commit"
    Write-Host "Mode: $Mode"
    Write-Host "Sources: $($resolvedSources.Count)"
    if ($protectValidationFilter) {
        Write-Host "Filtered Validation ($ValidationFilter): preliminary batch will use --no-history so selection uses pre-run history."
    }

    Write-Host "`n==> Runtime doctor"
    & $genreTest doctor
    if ($LASTEXITCODE -ne 0) {
        throw "genre-test doctor failed with exit code $LASTEXITCODE"
    }

    if (-not $SkipBatch) {
        for ($i = 0; $i -lt $resolvedSources.Count; $i++) {
            $sourcePath = $resolvedSources[$i]
            $sourceOut = Join-Path $batchRoot ("source_{0:D2}" -f ($i + 1))
            New-Item -ItemType Directory -Force -Path $sourceOut | Out-Null

            Write-Host "`n==> Ensemble batch [$($i + 1)/$($resolvedSources.Count)]: $sourcePath"
            $batchArgs = @(
                'batch', $sourcePath,
                '--out', $sourceOut,
                '--device', 'auto',
                '--mode', $Mode,
                '--semantic', 'auto',
                '--view', 'all',
                '--full-path'
            )
            if ($batchNoHistory) { $batchArgs += '--no-history' }
            & $genreTest @batchArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Batch failed for $sourcePath with exit code $LASTEXITCODE"
            }
        }
    }

    if (-not $SkipValidation) {
        Write-Host "`n==> Validation"
        $validationArgs = @('validate')
        $validationArgs += $resolvedSources
        $validationArgs += @(
            '--out', $validationRoot,
            '--device', 'auto',
            '--filter', $ValidationFilter
        )
        if ($CompareModes) {
            $validationArgs += '--compare-modes'
        } else {
            $validationArgs += @('--mode', $Mode)
        }
        & $genreTest @validationArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Validation failed with exit code $LASTEXITCODE"
        }
    }

    $elapsed = (Get-Date) - $started
    Write-Host "`n============================================================"
    Write-Host ' LARGE REGRESSION COMPLETE'
    Write-Host "Elapsed: $([math]::Round($elapsed.TotalMinutes, 2)) min"
    Write-Host "Results: $runRoot"
    Write-Host '============================================================'
} finally {
    Stop-Transcript | Out-Null
}
