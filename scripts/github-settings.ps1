[CmdletBinding()]
param(
    [ValidateSet('Apply','Check','Export')]
    [string]$Mode = 'Check',

    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\config\github\settings.json'),

    [switch]$InstallGh
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$File,
        [Parameter(Mandatory)][string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & $File @Arguments 2>&1
    $code = $LASTEXITCODE

    if (-not $AllowFailure -and $code -ne 0) {
        throw "$File $($Arguments -join ' ') failed with exit code $code`n$($output -join "`n")"
    }

    [pscustomobject]@{
        ExitCode = $code
        Output = ($output -join "`n")
    }
}

function Ensure-Gh {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        if (-not $InstallGh) {
            throw "GitHub CLI (gh) is not installed. Re-run with -InstallGh."
        }

        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            throw "GitHub CLI is missing and WinGet is unavailable."
        }

        Write-Host "Installing GitHub CLI..."
        $r = Invoke-Native winget @(
            'install', '--id', 'GitHub.cli', '-e',
            '--accept-source-agreements',
            '--accept-package-agreements'
        )
        Write-Host $r.Output

        $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                    [Environment]::GetEnvironmentVariable('Path','User')
    }

    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI is not available in PATH. Start a new PowerShell session and retry."
    }

    $auth = Invoke-Native gh @('auth','status') -AllowFailure
    if ($auth.ExitCode -ne 0) {
        throw @"
GitHub CLI is not authenticated.

Authenticate once:
  gh auth login

Then run this command again.
No repository settings were changed.
"@
    }
}

function Read-Config {
    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        throw "Config not found: $ConfigPath"
    }
    Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Gh-GetJson {
    param([Parameter(Mandatory)][string]$Endpoint)
    $r = Invoke-Native gh @('api', $Endpoint, '-H', 'X-GitHub-Api-Version: 2026-03-10')
    $r.Output | ConvertFrom-Json
}

function Gh-SendJson {
    param(
        [Parameter(Mandatory)][ValidateSet('PATCH','PUT')][string]$Method,
        [Parameter(Mandatory)][string]$Endpoint,
        [Parameter(Mandatory)]$Body
    )

    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        $Body | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $tmp -Encoding utf8NoBOM
        Invoke-Native gh @(
            'api',
            '--method', $Method,
            $Endpoint,
            '-H', 'X-GitHub-Api-Version: 2026-03-10',
            '--input', $tmp
        ) | Out-Null
    }
    finally {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}

function Compare-Properties {
    param(
        [Parameter(Mandatory)]$Expected,
        [Parameter(Mandatory)]$Actual,
        [Parameter(Mandatory)][string]$Section
    )

    $failed = $false
    foreach ($p in $Expected.PSObject.Properties) {
        $name = $p.Name
        $want = $p.Value

        if (-not ($Actual.PSObject.Properties.Name -contains $name)) {
            Write-Host ("FAIL {0}.{1}: property missing from API response" -f $Section, $name)
            $failed = $true
            continue
        }

        $have = $Actual.$name
        $wantJson = $want | ConvertTo-Json -Compress -Depth 10
        $haveJson = $have | ConvertTo-Json -Compress -Depth 10

        if ($wantJson -eq $haveJson) {
            Write-Host ("PASS {0}.{1} = {2}" -f $Section, $name, $haveJson)
        } else {
            Write-Host ("FAIL {0}.{1}: expected {2}, actual {3}" -f $Section, $name, $wantJson, $haveJson)
            $failed = $true
        }
    }
    return -not $failed
}

Ensure-Gh
$config = Read-Config
$repo = [string]$config.repository

if ([string]::IsNullOrWhiteSpace($repo) -or $repo -notmatch '^[^/]+/[^/]+$') {
    throw "Invalid repository in config: '$repo'"
}

$repoEndpoint = "repos/$repo"
$actionsEndpoint = "repos/$repo/actions/permissions"
$selectedActionsEndpoint = "repos/$repo/actions/permissions/selected-actions"
$workflowEndpoint = "repos/$repo/actions/permissions/workflow"

switch ($Mode) {
    'Apply' {
        Write-Host "Applying managed GitHub settings to $repo ..."

        Gh-SendJson PATCH $repoEndpoint $config.repository_settings
        Write-Host "Applied repository settings."

        Gh-SendJson PUT $actionsEndpoint $config.actions_permissions
        Write-Host "Applied Actions policy."

        if ($config.actions_permissions.allowed_actions -eq 'selected') {
            Gh-SendJson PUT $selectedActionsEndpoint $config.selected_actions
            Write-Host "Applied selected-actions policy."
        }

        Gh-SendJson PUT $workflowEndpoint $config.workflow_permissions
        Write-Host "Applied default GITHUB_TOKEN permissions."

        & $PSCommandPath -Mode Check -ConfigPath $ConfigPath
        exit $LASTEXITCODE
    }

    'Check' {
        Write-Host "Checking managed GitHub settings for $repo ..."
        $ok = $true

        $repoActual = Gh-GetJson $repoEndpoint
        if (-not (Compare-Properties $config.repository_settings $repoActual 'repository')) {
            $ok = $false
        }

        $actionsActual = Gh-GetJson $actionsEndpoint
        if (-not (Compare-Properties $config.actions_permissions $actionsActual 'actions')) {
            $ok = $false
        }

        if ($config.actions_permissions.allowed_actions -eq 'selected') {
            $selectedActual = Gh-GetJson $selectedActionsEndpoint
            if (-not (Compare-Properties $config.selected_actions $selectedActual 'selected_actions')) {
                $ok = $false
            }
        }

        $workflowActual = Gh-GetJson $workflowEndpoint
        if (-not (Compare-Properties $config.workflow_permissions $workflowActual 'workflow')) {
            $ok = $false
        }

        if ($ok) {
            Write-Host "RESULT: PASS - managed GitHub settings match config."
            exit 0
        }

        Write-Host "RESULT: FAIL - GitHub settings drift detected."
        exit 2
    }

    'Export' {
        $repoActual = Gh-GetJson $repoEndpoint
        $actionsActual = Gh-GetJson $actionsEndpoint
        $workflowActual = Gh-GetJson $workflowEndpoint

        $repoExport = [ordered]@{}
        foreach ($p in $config.repository_settings.PSObject.Properties) {
            if ($repoActual.PSObject.Properties.Name -contains $p.Name) {
                $repoExport[$p.Name] = $repoActual.($p.Name)
            }
        }

        $actionsExport = [ordered]@{}
        foreach ($p in $config.actions_permissions.PSObject.Properties) {
            if ($actionsActual.PSObject.Properties.Name -contains $p.Name) {
                $actionsExport[$p.Name] = $actionsActual.($p.Name)
            }
        }

        $selectedExport = [ordered]@{}
        if ($actionsActual.allowed_actions -eq 'selected') {
            $selectedActual = Gh-GetJson $selectedActionsEndpoint
            foreach ($p in $config.selected_actions.PSObject.Properties) {
                if ($selectedActual.PSObject.Properties.Name -contains $p.Name) {
                    $selectedExport[$p.Name] = $selectedActual.($p.Name)
                }
            }
        }

        $workflowExport = [ordered]@{}
        foreach ($p in $config.workflow_permissions.PSObject.Properties) {
            if ($workflowActual.PSObject.Properties.Name -contains $p.Name) {
                $workflowExport[$p.Name] = $workflowActual.($p.Name)
            }
        }

        $snapshot = [ordered]@{
            schema_version = 1
            repository = $repo
            exported_at_utc = [DateTime]::UtcNow.ToString('o')
            repository_settings = $repoExport
            actions_permissions = $actionsExport
            selected_actions = $selectedExport
            workflow_permissions = $workflowExport
        }

        $out = Join-Path (Split-Path -Parent $ConfigPath) 'settings.exported.json'
        $snapshot | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
        Write-Host "Exported managed settings to: $out"
    }
}
