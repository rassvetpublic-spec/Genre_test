[CmdletBinding()]
param(
    [switch]$ConfigureGit
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
try {
    if ($env:OS -eq 'Windows_NT') {
        [Console]::InputEncoding = $utf8
        [Console]::OutputEncoding = $utf8
    }
} catch { }
$OutputEncoding = $utf8
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:LESSCHARSET = 'utf-8'

if ($ConfigureGit) {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git -and (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
        & $git.Source -C $repoRoot config --local core.quotepath false
        if ($LASTEXITCODE -ne 0) { throw 'Failed to set core.quotepath.' }
        & $git.Source -C $repoRoot config --local i18n.commitEncoding utf-8
        if ($LASTEXITCODE -ne 0) { throw 'Failed to set i18n.commitEncoding.' }
        & $git.Source -C $repoRoot config --local i18n.logOutputEncoding utf-8
        if ($LASTEXITCODE -ne 0) { throw 'Failed to set i18n.logOutputEncoding.' }
    }
}
