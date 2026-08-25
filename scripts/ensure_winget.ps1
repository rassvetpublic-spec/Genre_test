# Windows PowerShell 5.1 compatible WinGet bootstrap for Genre_test portable.
[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

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
        $alias = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
        if (Test-Path -LiteralPath $alias -PathType Leaf) { return $alias }
    }

    try {
        $app = Get-AppxPackage -Name Microsoft.DesktopAppInstaller -ErrorAction SilentlyContinue |
            Sort-Object Version -Descending |
            Select-Object -First 1
        if ($app -and $app.InstallLocation) {
            $packageExe = Join-Path $app.InstallLocation 'winget.exe'
            if (Test-Path -LiteralPath $packageExe -PathType Leaf) { return $packageExe }
        }
    } catch {}

    return $null
}

$existing = Find-Winget
if ($existing) {
    Write-Host "WinGet OK: $existing"
    return
}

Write-Host 'WinGet was not found. Attempting official Microsoft repair...' -ForegroundColor Yellow

try {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    } catch {}

    $gallery = Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue
    if (-not $gallery) {
        Register-PSRepository -Default -ErrorAction Stop
        $gallery = Get-PSRepository -Name PSGallery -ErrorAction Stop
    }
    $previousPolicy = $gallery.InstallationPolicy

    try {
        if ($previousPolicy -ne 'Trusted') {
            Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction Stop
        }

        $nuget = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
        if (-not $nuget) {
            $installProvider = Get-Command Install-PackageProvider -ErrorAction Stop
            if ($installProvider.Parameters.ContainsKey('Scope')) {
                Install-PackageProvider -Name NuGet -Force -Scope CurrentUser -ErrorAction Stop | Out-Null
            } else {
                Install-PackageProvider -Name NuGet -Force -ErrorAction Stop | Out-Null
            }
        }

        Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery -Scope CurrentUser -AllowClobber -ErrorAction Stop | Out-Null
        Import-Module Microsoft.WinGet.Client -Force -ErrorAction Stop
        Repair-WinGetPackageManager -Force -Latest -ErrorAction Stop | Out-Null
    }
    finally {
        if ($previousPolicy -and $previousPolicy -ne 'Trusted') {
            try { Set-PSRepository -Name PSGallery -InstallationPolicy $previousPolicy -ErrorAction SilentlyContinue } catch {}
        }
    }

    Start-Sleep -Seconds 2
    $winget = Find-Winget
    if ($winget) {
        Write-Host "WinGet repaired successfully: $winget" -ForegroundColor Green
        & $winget --version
        return
    }

    throw 'Microsoft repair completed, but winget.exe is still not available.'
}
catch {
    Write-Host "[WARN] Automatic WinGet repair failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host 'Opening Microsoft Store App Installer as the final fallback...'
    try { Start-Process 'ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1' | Out-Null } catch {}
    Write-Host 'If Python and FFmpeg are already installed, Genre_test may still start without WinGet.'
    exit 2
}
