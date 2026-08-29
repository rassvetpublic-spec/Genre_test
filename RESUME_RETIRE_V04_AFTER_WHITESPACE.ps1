[CmdletBinding()]
param(
    [string]$Repository = 'rassvetpublic-spec/Genre_test',
    [string]$Branch = 'chore/retire-v0.4'
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

function Get-RepoRoot {
    $r = Invoke-Native git @('rev-parse','--show-toplevel')
    $root = $r.Output.Trim()
    if (-not $root) { throw "Could not resolve Git repository root." }
    return $root
}

function Ensure-Gh {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI (gh) is not installed."
    }

    $auth = Invoke-Native gh @('auth','status') -AllowFailure
    if ($auth.ExitCode -ne 0) {
        throw "GitHub CLI is not authenticated. Run: gh auth login"
    }
}

function Normalize-TextFile {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    try {
        $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    } catch {
        return
    }

    # Normalize all line endings to LF first.
    $text = $text -replace "`r`n", "`n"
    $text = $text -replace "`r", "`n"

    # Remove trailing spaces/tabs on every line.
    $lines = $text -split "`n", -1
    $lines = $lines | ForEach-Object { $_ -replace '[ `t]+$', '' }
    $text = $lines -join "`n"

    # Ensure exactly one terminal LF for non-empty text files.
    $text = $text.TrimEnd("`n") + "`n"

    [System.IO.File]::WriteAllText(
        $Path,
        $text,
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Get-GitHubObject {
    param([Parameter(Mandatory)][string]$Endpoint)

    $r = Invoke-Native gh @(
        'api', $Endpoint,
        '-H', 'X-GitHub-Api-Version: 2026-03-10'
    ) -AllowFailure

    if ($r.ExitCode -ne 0 -or -not $r.Output.Trim()) {
        return $null
    }

    return ($r.Output | ConvertFrom-Json)
}

function Remove-RetiredGitHubObjects {
    Ensure-Gh

    $release = Get-GitHubObject "repos/$Repository/releases/tags/v0.4.0"
    if ($null -ne $release) {
        Write-Host "Deleting GitHub Release v0.4.0 ..."
        Invoke-Native gh @(
            'api','--method','DELETE',
            "repos/$Repository/releases/$($release.id)",
            '-H','X-GitHub-Api-Version: 2026-03-10'
        ) | Out-Null
    } else {
        Write-Host "GitHub Release v0.4.0 already absent."
    }

    $tag = Get-GitHubObject "repos/$Repository/git/ref/tags/v0.4.0"
    if ($null -ne $tag) {
        Write-Host "Deleting Git tag v0.4.0 ..."
        Invoke-Native gh @(
            'api','--method','DELETE',
            "repos/$Repository/git/refs/tags/v0.4.0",
            '-H','X-GitHub-Api-Version: 2026-03-10'
        ) | Out-Null
    } else {
        Write-Host "Git tag v0.4.0 already absent."
    }
}

$root = Get-RepoRoot
Ensure-Gh

$current = (Invoke-Native git @('-C',$root,'branch','--show-current')).Output.Trim()
if ($current -ne $Branch) {
    throw "Expected current branch '$Branch', actual '$current'. This resume script is only for the interrupted cleanup branch."
}

Write-Host "Normalizing whitespace in staged/new text files..."

$status = Invoke-Native git @('-C',$root,'status','--porcelain','--untracked-files=all')
foreach ($line in ($status.Output -split "`n")) {
    if (-not $line.Trim() -or $line.Length -lt 4) { continue }

    $path = $line.Substring(3).Trim()
    if ($path.Contains(' -> ')) {
        $path = ($path -split ' -> ')[-1]
    }
    $path = $path.Replace('/', '\')

    if ($path -match '\.(zip|pdf|wav|mp3|flac|png|jpg|jpeg|webp)$') {
        continue
    }

    Normalize-TextFile (Join-Path $root $path)
}

Invoke-Native git @('-C',$root,'add','-A') | Out-Null

Write-Host "Running git diff --cached --check ..."
Invoke-Native git @('-C',$root,'diff','--cached','--check') | Out-Null
Write-Host "Whitespace check PASS."

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $python = 'python'
    } else {
        throw "Python not found."
    }
}

Write-Host "Running targeted regression tests..."
Invoke-Native $python @(
    '-m','pytest','-q',
    (Join-Path $root 'tests\test_cli_defaults.py'),
    (Join-Path $root 'tests\test_profile.py'),
    (Join-Path $root 'tests\test_release_bootstrap.py'),
    (Join-Path $root 'tests\test_regression_manifest.py')
) | Out-Null
Write-Host "Targeted regression tests PASS."

$pending = Invoke-Native git @('-C',$root,'diff','--cached','--quiet') -AllowFailure
if ($pending.ExitCode -eq 0) {
    throw "No staged cleanup changes found."
}

Write-Host "Committing cleanup..."
Invoke-Native git @(
    '-C',$root,
    'commit','-m','chore: retire v0.4 release artifacts'
) | Out-Null

Write-Host "Pushing cleanup branch..."
Invoke-Native git @('-C',$root,'push','-u','origin',$Branch) | Out-Null

$existing = Invoke-Native gh @(
    'pr','list',
    '--repo',$Repository,
    '--head',$Branch,
    '--state','open',
    '--json','number',
    '--jq','.[0].number'
) -AllowFailure

$prNumber = $existing.Output.Trim()

if (-not $prNumber) {
    $body = @"
## Summary

- retire v0.4 packaged release workflow and active release artifacts;
- keep regression coverage while removing v04-specific test filenames;
- align README/ROADMAP/ACTIVE_CURRENT with active 0.5.0.dev0 development;
- preserve version-neutral packaged bootstrap support;
- no direct push to main.

## Finalization

After CI passes and this PR is merged:
- delete GitHub Release v0.4.0;
- delete Git tag v0.4.0.
"@

    Invoke-Native gh @(
        'pr','create',
        '--repo',$Repository,
        '--base','main',
        '--head',$Branch,
        '--title','chore: retire v0.4 release artifacts',
        '--body',$body
    ) | Out-Null

    $prNumber = (Invoke-Native gh @(
        'pr','view',$Branch,
        '--repo',$Repository,
        '--json','number',
        '--jq','.number'
    )).Output.Trim()
}

if (-not $prNumber) {
    throw "Could not resolve cleanup PR number."
}

Write-Host "Cleanup PR: #$prNumber"

# Wait briefly until checks are registered, then watch them.
for ($attempt = 1; $attempt -le 24; $attempt++) {
    $probe = Invoke-Native gh @(
        'pr','checks',$prNumber,
        '--repo',$Repository
    ) -AllowFailure

    if ($probe.Output -notmatch '(?i)no checks') {
        break
    }

    Start-Sleep -Seconds 5
}

Write-Host "Watching CI for PR #$prNumber ..."
Invoke-Native gh @(
    'pr','checks',$prNumber,
    '--repo',$Repository,
    '--watch',
    '--fail-fast'
) | Out-Null

Write-Host "CI PASS. Squash-merging PR #$prNumber ..."
Invoke-Native gh @(
    'pr','merge',$prNumber,
    '--repo',$Repository,
    '--squash',
    '--delete-branch'
) | Out-Null

Invoke-Native git @('-C',$root,'switch','main') | Out-Null
Invoke-Native git @('-C',$root,'pull','--ff-only','origin','main') | Out-Null

$localBranch = Invoke-Native git @(
    '-C',$root,'show-ref','--verify','--quiet',"refs/heads/$Branch"
) -AllowFailure
if ($localBranch.ExitCode -eq 0) {
    Invoke-Native git @('-C',$root,'branch','-D',$Branch) | Out-Null
}

Remove-RetiredGitHubObjects

Write-Host ""
Write-Host "Verifying retired GitHub objects..."
if ($null -ne (Get-GitHubObject "repos/$Repository/releases/tags/v0.4.0")) {
    throw "GitHub Release v0.4.0 still exists."
}
if ($null -ne (Get-GitHubObject "repos/$Repository/git/ref/tags/v0.4.0")) {
    throw "Git tag v0.4.0 still exists."
}

Write-Host "PASS: GitHub Release v0.4.0 absent."
Write-Host "PASS: Git tag v0.4.0 absent."
Write-Host ""
Write-Host "RETIREMENT COMPLETE."
