# Windows PowerShell 5.1 compatible Microsoft Visual C++ Runtime bootstrap.
[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-VCRuntimeState {
    $paths = @(
        'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'
    )
    foreach ($path in $paths) {
        try {
            $item = Get-ItemProperty -Path $path -ErrorAction Stop
            if ($item.Installed -eq 1) {
                return [pscustomobject]@{
                    Installed = $true
                    Version = [string]$item.Version
                    Path = $path
                }
            }
        } catch {}
    }
    return $null
}

function Find-Winget {
    $command = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command winget -ErrorAction SilentlyContinue }
    if ($command) { return $command.Source }

    if ($env:LOCALAPPDATA) {
        $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

$state = Get-VCRuntimeState
if ($state) {
    Write-Host "Microsoft Visual C++ x64 Runtime OK: $($state.Version)"
    exit 0
}

Write-Host 'Microsoft Visual C++ 2015-2022 x64 Runtime was not found.' -ForegroundColor Yellow
$winget = Find-Winget
if (-not $winget) {
    throw 'VC++ Runtime is missing and winget is unavailable. WinGet recovery must succeed before continuing.'
}

Write-Host 'Installing Microsoft Visual C++ 2015-2022 x64 Runtime...'
& $winget install --id 'Microsoft.VCRedist.2015+.x64' --exact --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity
$code = $LASTEXITCODE
if ($code -ne 0 -and $code -ne 3010) {
    throw "winget failed to install Microsoft Visual C++ Runtime (exit code $code)."
}

Start-Sleep -Seconds 1
$state = Get-VCRuntimeState
if (-not $state) {
    throw 'Microsoft Visual C++ Runtime installation finished, but the x64 runtime is still not registered.'
}

Write-Host "Microsoft Visual C++ x64 Runtime installed: $($state.Version)" -ForegroundColor Green
exit 0
