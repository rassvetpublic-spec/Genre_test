[CmdletBinding()]
param(
    [ValidateSet('Check','Prepare','Full')]
    [string]$Mode = 'Check',
    [switch]$InstallGh,
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'

switch ($Mode) {
    'Check' {
        & (Join-Path $PSScriptRoot 'github-settings.ps1') -Mode Check -InstallGh:$InstallGh
        $settingsExit = $LASTEXITCODE

        & (Join-Path $PSScriptRoot 'retire-v04.ps1') -Mode Check -InstallGh:$InstallGh
        $retireExit = $LASTEXITCODE

        if ($settingsExit -ne 0 -or $retireExit -ne 0) { exit 2 }
        exit 0
    }

    'Prepare' {
        & (Join-Path $PSScriptRoot 'install-repo-guards.ps1')
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        & (Join-Path $PSScriptRoot 'github-settings.ps1') -Mode Apply -InstallGh:$InstallGh
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        & (Join-Path $PSScriptRoot 'retire-v04.ps1') -Mode Prepare -InstallGh:$InstallGh -SkipTests:$SkipTests
        exit $LASTEXITCODE
    }

    'Full' {
        & (Join-Path $PSScriptRoot 'retire-v04.ps1') -Mode Full -InstallGh:$InstallGh -SkipTests:$SkipTests
        exit $LASTEXITCODE
    }
}
