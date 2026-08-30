[CmdletBinding()]
param(
    [ValidateSet('Apply','Check')]
    [string]$Mode = 'Check',

    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\config\github\rulesets\protect-main.json')
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
        throw 'GitHub CLI (gh) is not installed.'
    }

    $auth = Invoke-Native gh @('auth','status') -AllowFailure
    if ($auth.ExitCode -ne 0) {
        throw "GitHub CLI is not authenticated. Run: gh auth login"
    }
}

function Gh-GetJson {
    param([Parameter(Mandatory)][string]$Endpoint)

    $r = Invoke-Native gh @(
        'api',
        $Endpoint,
        '-H', 'Accept: application/vnd.github+json',
        '-H', 'X-GitHub-Api-Version: 2022-11-28'
    )
    $r.Output | ConvertFrom-Json
}

function Gh-SendJson {
    param(
        [Parameter(Mandatory)][ValidateSet('POST','PUT')][string]$Method,
        [Parameter(Mandatory)][string]$Endpoint,
        [Parameter(Mandatory)]$Body
    )

    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        $Body | ConvertTo-Json -Depth 30 |
            Set-Content -LiteralPath $tmp -Encoding utf8NoBOM

        Invoke-Native gh @(
            'api',
            '--method', $Method,
            $Endpoint,
            '-H', 'Accept: application/vnd.github+json',
            '-H', 'X-GitHub-Api-Version: 2022-11-28',
            '--input', $tmp
        ) | Out-Null
    }
    finally {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}

function Get-SingleRule {
    param(
        [Parameter(Mandatory)]$Detail,
        [Parameter(Mandatory)][string]$Type
    )

    $matches = @($Detail.rules | Where-Object { $_.type -eq $Type })
    if ($matches.Count -ne 1) {
        throw "Expected exactly one ruleset rule '$Type', found $($matches.Count)."
    }
    $matches[0]
}

function Assert-Equal {
    param(
        [Parameter(Mandatory)][string]$Name,
        $Expected,
        $Actual
    )

    $want = $Expected | ConvertTo-Json -Compress -Depth 20
    $have = $Actual | ConvertTo-Json -Compress -Depth 20
    if ($want -ne $have) {
        throw "Ruleset drift: $Name expected $want, actual $have"
    }

    Write-Host "PASS $Name = $have"
}

Ensure-Gh

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Ruleset config not found: $ConfigPath"
}

$config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$repo = [string]$config.repository
$expected = $config.ruleset

if ([string]::IsNullOrWhiteSpace($repo) -or $repo -notmatch '^[^/]+/[^/]+$') {
    throw "Invalid repository in config: '$repo'"
}

$repoActual = Gh-GetJson "repos/$repo"
Assert-Equal 'repository.visibility' $config.repository_assertions.visibility $repoActual.visibility

$all = @(Gh-GetJson "repos/$repo/rulesets")
$matches = @($all | Where-Object { $_.name -eq $expected.name })

if ($Mode -eq 'Apply') {
    if ($repoActual.visibility -ne $config.repository_assertions.visibility) {
        throw "Refusing Ruleset Apply while repository visibility is '$($repoActual.visibility)'. Expected '$($config.repository_assertions.visibility)'. Visibility is check-only and will not be changed automatically."
    }

    if ($matches.Count -gt 1) {
        throw "More than one ruleset named '$($expected.name)' exists. Refusing to guess."
    }

    if ($matches.Count -eq 1) {
        $id = $matches[0].id
        Write-Host "Updating ruleset '$($expected.name)' (id=$id) ..."
        Gh-SendJson PUT "repos/$repo/rulesets/$id" $expected
    }
    else {
        Write-Host "Creating ruleset '$($expected.name)' ..."
        Gh-SendJson POST "repos/$repo/rulesets" $expected
    }

    & $PSCommandPath -Mode Check -ConfigPath $ConfigPath
    exit $LASTEXITCODE
}

if ($matches.Count -ne 1) {
    throw "Expected exactly one ruleset named '$($expected.name)', found $($matches.Count)."
}

$detail = Gh-GetJson "repos/$repo/rulesets/$($matches[0].id)"

Assert-Equal 'ruleset.name' $expected.name $detail.name
Assert-Equal 'ruleset.target' $expected.target $detail.target
Assert-Equal 'ruleset.enforcement' $expected.enforcement $detail.enforcement
Assert-Equal 'ruleset.conditions.ref_name.include' @($expected.conditions.ref_name.include) @($detail.conditions.ref_name.include)
Assert-Equal 'ruleset.conditions.ref_name.exclude' @($expected.conditions.ref_name.exclude) @($detail.conditions.ref_name.exclude)
Assert-Equal 'ruleset.bypass_actors' @($expected.bypass_actors) @($detail.bypass_actors)

foreach ($type in @('deletion','non_fast_forward','required_linear_history','pull_request','required_status_checks')) {
    $null = Get-SingleRule $detail $type
    Write-Host "PASS ruleset rule present: $type"
}

$expectedPr = Get-SingleRule $expected 'pull_request'
$actualPr = Get-SingleRule $detail 'pull_request'
Assert-Equal 'pull_request.required_approving_review_count' $expectedPr.parameters.required_approving_review_count $actualPr.parameters.required_approving_review_count
Assert-Equal 'pull_request.dismiss_stale_reviews_on_push' $expectedPr.parameters.dismiss_stale_reviews_on_push $actualPr.parameters.dismiss_stale_reviews_on_push
Assert-Equal 'pull_request.require_code_owner_review' $expectedPr.parameters.require_code_owner_review $actualPr.parameters.require_code_owner_review
Assert-Equal 'pull_request.require_last_push_approval' $expectedPr.parameters.require_last_push_approval $actualPr.parameters.require_last_push_approval
Assert-Equal 'pull_request.required_review_thread_resolution' $expectedPr.parameters.required_review_thread_resolution $actualPr.parameters.required_review_thread_resolution
Assert-Equal 'pull_request.allowed_merge_methods' @($expectedPr.parameters.allowed_merge_methods) @($actualPr.parameters.allowed_merge_methods)

$expectedChecks = Get-SingleRule $expected 'required_status_checks'
$actualChecks = Get-SingleRule $detail 'required_status_checks'
Assert-Equal 'required_status_checks.strict' $expectedChecks.parameters.strict_required_status_checks_policy $actualChecks.parameters.strict_required_status_checks_policy
Assert-Equal 'required_status_checks.do_not_enforce_on_create' $expectedChecks.parameters.do_not_enforce_on_create $actualChecks.parameters.do_not_enforce_on_create

$wantContexts = @($expectedChecks.parameters.required_status_checks | ForEach-Object { $_.context } | Sort-Object)
$haveContexts = @($actualChecks.parameters.required_status_checks | ForEach-Object { $_.context } | Sort-Object)
Assert-Equal 'required_status_checks.contexts' $wantContexts $haveContexts

if ($detail.current_user_can_bypass -and $detail.current_user_can_bypass -ne 'never') {
    throw "Ruleset drift: current_user_can_bypass is '$($detail.current_user_can_bypass)', expected 'never' or absent."
}
Write-Host "PASS current_user_can_bypass = $($detail.current_user_can_bypass)"

Write-Host 'RESULT: PASS - server-side main Ruleset matches repository contract.'
exit 0
