[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Run this script inside the Genre_test Git working tree."
}

$repoRoot = $repoRoot.Trim()
$hook = Join-Path $repoRoot '.githooks\pre-push'

if (-not (Test-Path -LiteralPath $hook)) {
    throw "Tracked hook not found: $hook"
}

& git -C $repoRoot config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
    throw "Failed to set core.hooksPath."
}

$actual = (& git -C $repoRoot config --get core.hooksPath).Trim()
if ($actual -ne '.githooks') {
    throw "core.hooksPath verification failed: '$actual'"
}

Write-Host "Installed repository Git guard."
Write-Host "Direct local pushes to refs/heads/main are blocked in this clone."
