#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$NoInstall,
    [switch]$Required
)

$ErrorActionPreference = 'Stop'

function Find-FFmpeg {
    $command = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command ffmpeg -ErrorAction SilentlyContinue
    }
    if ($command) {
        return $command.Source
    }

    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($env:LOCALAPPDATA) {
        $candidates.Add((Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\ffmpeg.exe'))
    }
    if ($env:USERPROFILE) {
        $candidates.Add((Join-Path $env:USERPROFILE 'scoop\shims\ffmpeg.exe'))
    }
    if ($env:ProgramData) {
        $candidates.Add((Join-Path $env:ProgramData 'chocolatey\bin\ffmpeg.exe'))
    }
    if ($env:ProgramFiles) {
        $candidates.Add((Join-Path $env:ProgramFiles 'ffmpeg\bin\ffmpeg.exe'))
    }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate -PathType Leaf)) {
            return (Resolve-Path $candidate).Path
        }
    }
    return $null
}

function Add-FFmpegDirectoryToProcessPath {
    param([Parameter(Mandatory)] [string]$FFmpegPath)

    $directory = Split-Path -Parent $FFmpegPath
    $pathEntries = @($env:Path -split ';' | Where-Object { $_ })
    if ($pathEntries -notcontains $directory) {
        $env:Path = "$directory;$env:Path"
    }
}

$ffmpeg = Find-FFmpeg
if ($ffmpeg) {
    Add-FFmpegDirectoryToProcessPath -FFmpegPath $ffmpeg
    Write-Host "FFmpeg found: $ffmpeg"
    & $ffmpeg -version | Select-Object -First 1
    return
}

if ($NoInstall) {
    $message = 'FFmpeg was not found. Automatic installation was disabled.'
    if ($Required) { throw $message }
    Write-Warning $message
    return
}

if (-not $IsWindows) {
    $message = 'FFmpeg was not found. Automatic FFmpeg installation is currently implemented for Windows/winget only.'
    if ($Required) { throw $message }
    Write-Warning $message
    return
}

$winget = Get-Command winget.exe -ErrorAction SilentlyContinue
if (-not $winget) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
}
if (-not $winget) {
    $message = @'
FFmpeg is missing and winget is unavailable.
Install FFmpeg manually, then verify:
  ffmpeg -version
'@
    if ($Required) { throw $message }
    Write-Warning $message
    return
}

Write-Host 'FFmpeg not found. Installing Gyan.FFmpeg with winget...'
& $winget.Source install --id Gyan.FFmpeg --exact --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity
$installExitCode = $LASTEXITCODE
if ($installExitCode -ne 0) {
    $message = "winget failed to install Gyan.FFmpeg (exit code $installExitCode)."
    if ($Required) { throw $message }
    Write-Warning $message
    return
}

# WinGet portable packages expose command aliases here. Add it immediately so
# the current setup/upgrade process does not need a new PowerShell window.
if ($env:LOCALAPPDATA) {
    $wingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
    if (Test-Path $wingetLinks -PathType Container) {
        if (@($env:Path -split ';') -notcontains $wingetLinks) {
            $env:Path = "$wingetLinks;$env:Path"
        }
    }
}

Start-Sleep -Milliseconds 500
$ffmpeg = Find-FFmpeg
if (-not $ffmpeg) {
    $message = @'
winget reported a successful FFmpeg install, but ffmpeg.exe is still not visible.
Open a new PowerShell 7 window and run:
  ffmpeg -version
  .\.venv\Scripts\genre-test.exe doctor
'@
    if ($Required) { throw $message }
    Write-Warning $message
    return
}

Add-FFmpegDirectoryToProcessPath -FFmpegPath $ffmpeg
Write-Host "FFmpeg installed: $ffmpeg"
& $ffmpeg -version | Select-Object -First 1
