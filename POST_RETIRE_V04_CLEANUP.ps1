[CmdletBinding()]
param(
    [string]$RepoRoot = 'C:\GIT\Genre_test',
    [switch]$MTD
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Repository = 'rassvetpublic-spec/Genre_test'
$RetiredTag = 'v0.4.0'
$RetireBranch = 'chore/retire-v0.4'
$CleanupBranch = 'chore/cleanup-retirement-bootstrap'

# Permanent governance files intentionally kept:
#   .githooks/pre-push
#   config/github/settings.json
#   scripts/github-settings.ps1
#   scripts/install-repo-guards.ps1
#   CHECK_GOVERNANCE.cmd
#
# PRs and Actions history are audit evidence and are intentionally NOT deleted.

$TrackedOneOffFiles = @(
    'FULL_GOVERNANCE_AND_RETIRE_V04.cmd',
    'PREPARE_GOVERNANCE_AND_RETIRE_V04.cmd',
    'MANIFEST_SHA256.txt',
    'README_FIRST.md',
    'RESUME_RETIRE_V04_AFTER_WHITESPACE.ps1',
    'RESUME_RETIRE_V04_AFTER_WHITESPACE_FIX.ps1',
    'HOTFIX_GOVERNANCE_HAS_DOWNLOADS.ps1',
    'scripts/retire-v04.ps1',
    'scripts/repo-governance.ps1'
)

$LocalTempPatterns = @(
    'Genre_test_Governance_Retire_v04*.zip',
    'HOTFIX_GOVERNANCE_HAS_DOWNLOADS.ps1',
    'RESUME_RETIRE_V04_AFTER_WHITESPACE*.ps1',
    'POST_RETIRE_V04_CLEANUP.ps1'
)

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$File,
        [Parameter(Mandatory)][string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & $File @Arguments 2>&1
    $code = $LASTEXITCODE
    $text = ($output | ForEach-Object { "$_" }) -join "`n"

    if (-not $AllowFailure -and $code -ne 0) {
        throw "$File $($Arguments -join ' ') failed with exit code $code`n$text"
    }

    [pscustomobject]@{
        ExitCode = $code
        Output = $text
    }
}

function Assert-GhAuth {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw 'GitHub CLI (gh) is not installed.'
    }
    $auth = Invoke-Native gh @('auth','status') -AllowFailure
    if ($auth.ExitCode -ne 0) {
        throw "GitHub CLI is not authenticated. Run: gh auth login"
    }
}

function Test-RemoteRef {
    param([Parameter(Mandatory)][string]$Ref)
    $r = Invoke-Native git @('-C',$RepoRoot,'ls-remote','--exit-code','origin',$Ref) -AllowFailure
    return $r.ExitCode -eq 0
}

function Remove-LocalTemps {
    foreach ($pattern in $LocalTempPatterns) {
        Get-ChildItem -LiteralPath $RepoRoot -Filter $pattern -Force -ErrorAction SilentlyContinue |
            ForEach-Object {
                # Do not delete this running script until process exit.
                if ($PSCommandPath -and $_.FullName -eq $PSCommandPath) {
                    Write-Host "DEFER self-delete: $($_.Name)"
                    return
                }
                Remove-Item -LiteralPath $_.FullName -Force -Recurse
                Write-Host "LOCAL REMOVE $($_.Name)"
            }
    }
}

function Assert-NoUnrelatedTrackedChanges {
    $status = Invoke-Native git @('-C',$RepoRoot,'status','--porcelain','--untracked-files=all')
    $bad = @()

    foreach ($line in ($status.Output -split "`n")) {
        if (-not $line) { continue }

        $code = $line.Substring(0,2)
        $path = $line.Substring(3).Trim('"')

        # Untracked package helpers are allowed; they will be deleted later.
        if ($code -eq '??') {
            $name = Split-Path -Leaf $path
            $allowed = $false
            foreach ($pattern in $LocalTempPatterns) {
                if ($name -like $pattern) { $allowed = $true; break }
            }
            if ($allowed) { continue }
        }

        $bad += $line
    }

    if ($bad.Count -gt 0) {
        throw "Working tree contains unrelated changes. Commit/stash them before cleanup:`n$($bad -join "`n")"
    }
}

function Assert-RetirementMerged {
    $prJson = Invoke-Native gh @(
        'pr','list',
        '--repo',$Repository,
        '--head',$RetireBranch,
        '--state','all',
        '--limit','1',
        '--json','number,state,mergedAt,url'
    )

    if (-not $prJson.Output.Trim()) {
        throw "Retirement PR for $RetireBranch was not found."
    }

    $pr = $prJson.Output | ConvertFrom-Json
    if ($pr.Count -eq 0 -or -not $pr[0].mergedAt) {
        $number = if ($pr.Count -gt 0) { $pr[0].number } else { '?' }
        throw "Retirement PR #$number is not merged yet. Do not run post-cleanup before retirement CI/merge completes."
    }

    Write-Host "PASS retirement PR #$($pr[0].number) is merged."
}

function Assert-MainRetiredArtifactsAbsent {
    $blocked = @(
        '.github/workflows/release-v0.4.0.yml',
        'RELEASE_NOTES_0.4.0.md',
        'releases/Genre_test_0.4.0_portable.zip',
        'releases/RELEASE_NOTES_0.4.0.md'
    )

    foreach ($rel in $blocked) {
        if (Test-Path -LiteralPath (Join-Path $RepoRoot $rel)) {
            throw "Refusing remote v0.4 cleanup: main still contains '$rel'."
        }
    }

    Write-Host 'PASS active v0.4 release artifacts are absent from main.'
}

function Remove-GitHubReleaseAndTag {
    $release = Invoke-Native gh @(
        'api',"repos/$Repository/releases/tags/$RetiredTag",
        '-H','X-GitHub-Api-Version: 2022-11-28',
        '--jq','.id'
    ) -AllowFailure

    if ($release.ExitCode -eq 0 -and $release.Output.Trim()) {
        $releaseId = $release.Output.Trim()
        Write-Host "GITHUB REMOVE Release $RetiredTag (id=$releaseId)"
        Invoke-Native gh @(
            'api','--method','DELETE',
            "repos/$Repository/releases/$releaseId",
            '-H','X-GitHub-Api-Version: 2022-11-28'
        ) | Out-Null
    } else {
        Write-Host "PASS GitHub Release $RetiredTag already absent."
    }

    $tag = Invoke-Native gh @(
        'api',"repos/$Repository/git/ref/tags/$RetiredTag",
        '-H','X-GitHub-Api-Version: 2022-11-28'
    ) -AllowFailure

    if ($tag.ExitCode -eq 0) {
        Write-Host "GITHUB REMOVE tag $RetiredTag"
        Invoke-Native gh @(
            'api','--method','DELETE',
            "repos/$Repository/git/refs/tags/$RetiredTag",
            '-H','X-GitHub-Api-Version: 2022-11-28'
        ) | Out-Null
    } else {
        Write-Host "PASS Git tag $RetiredTag already absent."
    }
}

function Remove-RetirementBranches {
    if (Test-RemoteRef "refs/heads/$RetireBranch") {
        Write-Host "GITHUB REMOVE remote branch $RetireBranch"
        Invoke-Native git @('-C',$RepoRoot,'push','origin','--delete',$RetireBranch) | Out-Null
    } else {
        Write-Host "PASS remote branch $RetireBranch already absent."
    }

    $local = Invoke-Native git @('-C',$RepoRoot,'show-ref','--verify','--quiet',"refs/heads/$RetireBranch") -AllowFailure
    if ($local.ExitCode -eq 0) {
        Write-Host "LOCAL REMOVE branch $RetireBranch"
        Invoke-Native git @('-C',$RepoRoot,'branch','-D',$RetireBranch) | Out-Null
    }
}

function Write-PermanentCheckWrapper {
    $path = Join-Path $RepoRoot 'CHECK_GOVERNANCE.cmd'
    $content = @'
@echo off
setlocal
cd /d "%~dp0"

pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\github-settings.ps1" -Mode Check
if errorlevel 1 exit /b %ERRORLEVEL%

git config --get core.hooksPath | findstr /x /c:".githooks" >nul
if errorlevel 1 (
    echo FAIL local core.hooksPath is not .githooks
    exit /b 2
)

if not exist ".githooks\pre-push" (
    echo FAIL .githooks\pre-push is missing
    exit /b 2
)

echo PASS permanent repository governance checks
exit /b 0
'@
    [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
}

function Prepare-CleanupPR {
    $oneOffPresent = $false
    foreach ($rel in $TrackedOneOffFiles) {
        $tracked = Invoke-Native git @('-C',$RepoRoot,'ls-files','--error-unmatch',$rel) -AllowFailure
        if ($tracked.ExitCode -eq 0) {
            $oneOffPresent = $true
            break
        }
    }

    # repo-governance.ps1 currently makes CHECK_GOVERNANCE retirement-specific.
    $checkNeedsRewrite = $false
    $checkPath = Join-Path $RepoRoot 'CHECK_GOVERNANCE.cmd'
    if (Test-Path -LiteralPath $checkPath) {
        $checkText = Get-Content -LiteralPath $checkPath -Raw -Encoding UTF8
        if ($checkText -match 'repo-governance\.ps1') {
            $checkNeedsRewrite = $true
        }
    }

    if (-not $oneOffPresent -and -not $checkNeedsRewrite) {
        Write-Host 'PASS no tracked retirement-bootstrap files remain.'
        return $null
    }

    $existingRemote = Test-RemoteRef "refs/heads/$CleanupBranch"
    if ($existingRemote) {
        throw "Cleanup branch '$CleanupBranch' already exists remotely. Inspect it instead of creating a duplicate."
    }

    Write-Host "Preparing cleanup branch $CleanupBranch ..."
    Invoke-Native git @('-C',$RepoRoot,'switch','-c',$CleanupBranch,'origin/main') | Out-Null

    foreach ($rel in $TrackedOneOffFiles) {
        $tracked = Invoke-Native git @('-C',$RepoRoot,'ls-files','--error-unmatch',$rel) -AllowFailure
        if ($tracked.ExitCode -eq 0) {
            Remove-Item -LiteralPath (Join-Path $RepoRoot $rel) -Force -Recurse -ErrorAction SilentlyContinue
            Write-Host "REPO REMOVE $rel"
        }
    }

    Write-PermanentCheckWrapper

    Invoke-Native git @('-C',$RepoRoot,'add','-A') | Out-Null
    Invoke-Native git @('-C',$RepoRoot,'-c','core.whitespace=cr-at-eol','diff','--cached','--check') | Out-Null

    $quiet = Invoke-Native git @('-C',$RepoRoot,'diff','--cached','--quiet') -AllowFailure
    if ($quiet.ExitCode -eq 0) {
        Write-Host 'PASS no cleanup commit is required.'
        Invoke-Native git @('-C',$RepoRoot,'switch','main') | Out-Null
        Invoke-Native git @('-C',$RepoRoot,'branch','-D',$CleanupBranch) | Out-Null
        return $null
    }

    Invoke-Native git @('-C',$RepoRoot,'commit','-m','chore: remove retirement bootstrap artifacts') | Out-Null
    Invoke-Native git @('-C',$RepoRoot,'push','-u','origin',$CleanupBranch) | Out-Null

    $body = @"
## Summary

Removes one-off v0.4 retirement/bootstrap helpers after the retirement operation completed.

Permanent governance intentionally remains:
- `.githooks/pre-push`
- `config/github/settings.json`
- `scripts/github-settings.ps1`
- `scripts/install-repo-guards.ps1`
- `CHECK_GOVERNANCE.cmd`

No production/audio behavior changes.
No historical PR/Actions audit evidence is deleted.
"@

    Invoke-Native gh @(
        'pr','create',
        '--repo',$Repository,
        '--base','main',
        '--head',$CleanupBranch,
        '--title','chore: remove retirement bootstrap artifacts',
        '--body',$body
    ) | Out-Null

    $number = (Invoke-Native gh @(
        'pr','view',$CleanupBranch,
        '--repo',$Repository,
        '--json','number',
        '--jq','.number'
    )).Output.Trim()

    if (-not $number) {
        throw 'Could not resolve cleanup PR number.'
    }

    Write-Host "Cleanup PR created: #$number"
    return $number
}

function Complete-CleanupPR {
    param([Parameter(Mandatory)][string]$Number)

    # Wait briefly for GitHub to attach checks.
    for ($i = 1; $i -le 24; $i++) {
        $probe = Invoke-Native gh @('pr','checks',$Number,'--repo',$Repository) -AllowFailure
        if ($probe.Output -notmatch '(?i)no checks') { break }
        Start-Sleep -Seconds 5
    }

    Write-Host "Watching CI for cleanup PR #$Number ..."
    Invoke-Native gh @(
        'pr','checks',$Number,
        '--repo',$Repository,
        '--watch',
        '--fail-fast'
    ) | Out-Null

    Write-Host "Squash-merging cleanup PR #$Number ..."
    Invoke-Native gh @(
        'pr','merge',$Number,
        '--repo',$Repository,
        '--squash',
        '--delete-branch'
    ) | Out-Null

    Invoke-Native git @('-C',$RepoRoot,'switch','main') | Out-Null
    Invoke-Native git @('-C',$RepoRoot,'pull','--ff-only','origin','main') | Out-Null

    $local = Invoke-Native git @('-C',$RepoRoot,'show-ref','--verify','--quiet',"refs/heads/$CleanupBranch") -AllowFailure
    if ($local.ExitCode -eq 0) {
        Invoke-Native git @('-C',$RepoRoot,'branch','-D',$CleanupBranch) | Out-Null
    }
}

function Final-Verify {
    $release = Invoke-Native gh @(
        'api',"repos/$Repository/releases/tags/$RetiredTag",
        '-H','X-GitHub-Api-Version: 2022-11-28'
    ) -AllowFailure
    if ($release.ExitCode -eq 0) {
        throw "Final verification failed: GitHub Release $RetiredTag still exists."
    }

    $tag = Invoke-Native gh @(
        'api',"repos/$Repository/git/ref/tags/$RetiredTag",
        '-H','X-GitHub-Api-Version: 2022-11-28'
    ) -AllowFailure
    if ($tag.ExitCode -eq 0) {
        throw "Final verification failed: Git tag $RetiredTag still exists."
    }

    if (Test-RemoteRef "refs/heads/$RetireBranch") {
        throw "Final verification failed: remote branch $RetireBranch still exists."
    }

    if ($MTD) {
        foreach ($rel in $TrackedOneOffFiles) {
            $tracked = Invoke-Native git @('-C',$RepoRoot,'ls-files','--error-unmatch',$rel) -AllowFailure
            if ($tracked.ExitCode -eq 0) {
                throw "Final verification failed: one-off file is still tracked: $rel"
            }
        }
    }

    Write-Host ''
    Write-Host 'POST-RETIRE CLEANUP PASS.'
    Write-Host 'v0.4 Release/tag absent; retirement branch absent; local package helpers removed.'
    if ($MTD) {
        Write-Host 'One-off retirement bootstrap files are also removed from main via cleanup PR.'
    }
}

Set-Location -LiteralPath $RepoRoot

$remote = (Invoke-Native git @('-C',$RepoRoot,'remote','get-url','origin')).Output.Trim()
if ($remote -notmatch 'rassvetpublic-spec/Genre_test(?:\.git)?$') {
    throw "Wrong repository: $remote"
}

Assert-GhAuth
Assert-NoUnrelatedTrackedChanges
Assert-RetirementMerged

Invoke-Native git @('-C',$RepoRoot,'fetch','origin','--prune') | Out-Null

$current = (Invoke-Native git @('-C',$RepoRoot,'branch','--show-current')).Output.Trim()
if ($current -ne 'main') {
    Invoke-Native git @('-C',$RepoRoot,'switch','main') | Out-Null
}
Invoke-Native git @('-C',$RepoRoot,'pull','--ff-only','origin','main') | Out-Null

Assert-MainRetiredArtifactsAbsent
Remove-GitHubReleaseAndTag
Remove-RetirementBranches
Remove-LocalTemps

$cleanupPr = Prepare-CleanupPR
if ($cleanupPr -and $MTD) {
    Complete-CleanupPR -Number $cleanupPr
} elseif ($cleanupPr) {
    Write-Host ''
    Write-Host "Cleanup PR #$cleanupPr is ready. It was NOT merged because -MTD was not supplied."
    Write-Host "After review/CI, rerun this script with -MTD to complete repository cleanup."
    exit 0
}

Final-Verify

# Self-delete only at the very end if the script lives in RepoRoot.
if ($PSCommandPath -and (Split-Path -Parent $PSCommandPath) -eq (Resolve-Path $RepoRoot).Path) {
    $self = $PSCommandPath
    Write-Host "Scheduling local self-delete: $(Split-Path -Leaf $self)"
    Start-Process -FilePath 'cmd.exe' -ArgumentList @(
        '/c',
        "ping 127.0.0.1 -n 2 >nul & del /f /q `"$self`""
    ) -WindowStyle Hidden
}
