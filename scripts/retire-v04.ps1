[CmdletBinding()]
param(
    [ValidateSet('Check','Prepare','FinalizeGitHub','Full')]
    [string]$Mode = 'Check',

    [string]$Repository = 'rassvetpublic-spec/Genre_test',
    [string]$Branch = 'chore/retire-v0.4',
    [switch]$InstallGh,
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RetiredTag = 'v0.4.0'
$CurrentDevVersion = '0.5.0.dev0'

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
        throw "GitHub CLI is not authenticated. Run: gh auth login"
    }
}

function Get-RepoRoot {
    $r = Invoke-Native git @('rev-parse','--show-toplevel')
    $root = $r.Output.Trim()
    if (-not $root) { throw "Could not resolve Git repository root." }
    return $root
}

function Assert-CorrectRepository {
    param([Parameter(Mandatory)][string]$Root)

    $remote = Invoke-Native git @('-C', $Root, 'remote', 'get-url', 'origin')
    if ($remote.Output -notmatch 'rassvetpublic-spec/Genre_test(?:\.git)?$') {
        throw "origin does not point to rassvetpublic-spec/Genre_test: $($remote.Output)"
    }
}

function Assert-CleanWorkingTree {
    param([Parameter(Mandatory)][string]$Root)

    $allowedBootstrapPaths = @(
        '.githooks/pre-push',
        'CHECK_GOVERNANCE.cmd',
        'FULL_GOVERNANCE_AND_RETIRE_V04.cmd',
        'MANIFEST_SHA256.txt',
        'PREPARE_GOVERNANCE_AND_RETIRE_V04.cmd',
        'README_FIRST.md',
        'config/github/settings.json',
        'scripts/github-settings.ps1',
        'scripts/install-repo-guards.ps1',
        'scripts/repo-governance.ps1',
        'scripts/retire-v04.ps1'
    )

    $s = Invoke-Native git @('-C', $Root, 'status', '--porcelain', '--untracked-files=all')
    $unexpected = @()

    foreach ($line in ($s.Output -split "`n")) {
        if (-not $line.Trim()) { continue }

        # porcelain v1: XY<space>path
        if ($line.Length -lt 4) {
            $unexpected += $line
            continue
        }

        $path = $line.Substring(3).Trim()

        # Handle the "old -> new" shape defensively.
        if ($path.Contains(' -> ')) {
            $path = ($path -split ' -> ')[-1]
        }

        $path = $path.Replace('\', '/')

        if ($allowedBootstrapPaths -notcontains $path) {
            $unexpected += $line
        }
    }

    if ($unexpected.Count -gt 0) {
        throw @"
Working tree contains changes unrelated to this governance package.

Commit/stash those changes first. The cleanup refuses to mix with unrelated work.

$($unexpected -join "`n")
"@
    }

    if ($s.Output.Trim()) {
        Write-Host "Working tree contains only expected governance-package files; continuing."
    }
}

function Remove-TrackedPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$RelativePath
    )

    $full = Join-Path $Root $RelativePath
    if (Test-Path -LiteralPath $full) {
        Invoke-Native git @('-C', $Root, 'rm', '-f', '--', $RelativePath) | Out-Null
        Write-Host "REMOVE $RelativePath"
    }
}

function Move-TrackedPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Old,
        [Parameter(Mandatory)][string]$New
    )

    $oldFull = Join-Path $Root $Old
    $newFull = Join-Path $Root $New

    if (Test-Path -LiteralPath $oldFull) {
        if (Test-Path -LiteralPath $newFull) {
            throw "Cannot rename '$Old' to '$New': target already exists."
        }
        Invoke-Native git @('-C', $Root, 'mv', '--', $Old, $New) | Out-Null
        Write-Host "RENAME $Old -> $New"
    }
}

function Replace-Literal {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Old,
        [Parameter(Mandatory)][string]$New,
        [switch]$Optional
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        if ($Optional) { return }
        throw "File not found: $Path"
    }

    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if (-not $text.Contains($Old)) {
        if ($Optional) { return }
        throw "Expected text not found in $Path : $Old"
    }

    $updated = $text.Replace($Old, $New)
    Set-Content -LiteralPath $Path -Value $updated -Encoding utf8NoBOM -NoNewline
}

function Replace-Regex {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Pattern,
        [Parameter(Mandatory)][string]$Replacement,
        [switch]$Optional
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        if ($Optional) { return }
        throw "File not found: $Path"
    }

    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $updated = [regex]::Replace(
        $text,
        $Pattern,
        $Replacement,
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )

    if ($updated -eq $text) {
        if ($Optional) { return }
        throw "Expected regex did not match in $Path : $Pattern"
    }

    Set-Content -LiteralPath $Path -Value $updated -Encoding utf8NoBOM -NoNewline
}

function Write-GenericPortableDocs {
    param([Parameter(Mandatory)][string]$Root)

    $english = @"
Genre_test portable packaging

STATUS
------
There is currently no published stable portable release.
The active development version is read from pyproject.toml.

START
-----
1. Extract a future packaged build to a normal local folder.
2. Do not run directly from inside a ZIP.
3. Start only Genre_test_START.cmd.
4. Internet access may be required for first-time dependency/model setup.

RUNTIME BASELINE
----------------
- Windows 10/11 x64
- Windows PowerShell 5.1 for packaged bootstrap
- Python 3.11 / 3.12 / 3.13 x64
- PyTorch 2.12.1
- NVIDIA CUDA 13.0 / cu130 when NVIDIA hardware is used
- CPU-only mode supported
- FFmpeg
- isolated project .venv

The package must not bundle another project's virtual environment.
Normal pip and Hugging Face user caches may be reused.

MODELS
------
Pinned public analysis models are downloaded on demand.
Third-party model provenance remains documented separately.

INTEGRITY
---------
A future published package must provide its own checksum manifest.
Do not use checksum files from retired releases.

Current development line: Genre_test $CurrentDevVersion
"@

    $russian = @"
Genre_test — упаковка portable

СТАТУС
------
Сейчас опубликованного стабильного portable-релиза нет.
Активная версия разработки берётся из pyproject.toml.

ЗАПУСК
------
1. Будущую packaged-сборку распаковать в обычный локальный каталог.
2. Не запускать программу прямо из ZIP.
3. Пользовательская точка входа — только Genre_test_START.cmd.
4. При первой настройке зависимостей/моделей может потребоваться интернет.

БАЗОВАЯ СРЕДА
-------------
- Windows 10/11 x64
- Windows PowerShell 5.1 для packaged bootstrap
- Python 3.11 / 3.12 / 3.13 x64
- PyTorch 2.12.1
- NVIDIA CUDA 13.0 / cu130 при использовании NVIDIA
- CPU-only режим поддерживается
- FFmpeg
- изолированная .venv проекта

В пакет нельзя переносить виртуальную среду другого проекта.
Обычные пользовательские кэши pip и Hugging Face могут переиспользоваться.

МОДЕЛИ
------
Закреплённые публичные модели анализа загружаются по необходимости.
Provenance сторонних моделей документируется отдельно.

ЦЕЛОСТНОСТЬ
-----------
Будущий опубликованный пакет должен иметь собственный checksum manifest.
Checksum-файлы удалённых релизов использовать нельзя.

Активная линия разработки: Genre_test $CurrentDevVersion
"@

    Set-Content -LiteralPath (Join-Path $Root 'PORTABLE_README.txt') -Value $english -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $Root 'README_RU.txt') -Value $russian -Encoding utf8NoBOM
}

function Update-CurrentDocs {
    param([Parameter(Mandatory)][string]$Root)

    $readme = Join-Path $Root 'README.md'
    Replace-Literal $readme '**Latest stable release: 0.4.0**' '**Published stable release: none; active development line: 0.5.0.dev0**' -Optional
    Replace-Literal $readme '## Stable v0.4.0 analysis baseline' '## Current analysis baseline' -Optional
    Replace-Literal $readme 'Ordinary v0.4/v0.5 analysis and retrieval must not require Ozone or REAPER.' 'Ordinary analysis and retrieval must not require Ozone or REAPER.' -Optional

    $portableReplacement = @"
### Portable packaging

No packaged stable release is currently published. The former portable release
has been retired from the active repository and from GitHub Releases/Tags.

`Genre_test_START.cmd` retains packaged-mode bootstrap support for a future
release, but there is no current release archive to download.

## GUI
"@
    Replace-Regex $readme '(?ms)^### Portable release\s+.*?^## GUI\s*$' $portableReplacement -Optional

    $evidenceReplacement = @"
## Current development evidence

The core analysis/runtime baseline remains covered by Windows ensemble,
Validation, Safe Stop, CUDA/Blackwell, Ruff, pytest and PowerShell/runtime gates.
Those checks are development evidence and are not advertised as an active
packaged release.

## Integrated studio-finish direction
"@
    Replace-Regex $readme '(?ms)^## Current release evidence\s+.*?^## Integrated studio-finish direction\s*$' $evidenceReplacement -Optional

    $roadmap = Join-Path $Root 'ROADMAP.md'
    $roadmapReplacement = @"
## Current development line

**0.5.0.dev0 — active development; no packaged stable release is currently published**

Genre_test currently provides the core local music profiling and regression system:

```text
Audio
  -> MAEST Discogs519 fine-style evidence
  -> AudioSet AST semantic evidence
  -> BPM / key / native source metadata
  -> calibrated evidence fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor outputs
  -> history / Validation / build comparison
```

The former packaged release line is retired. Core analysis behavior remains a
regression baseline while v0.5 retrieval development proceeds.

## ACTIVE: v0.5
"@
    Replace-Regex $roadmap '(?ms)^## Current release\s+.*?^## ACTIVE: v0\.5[^\r\n]*\r?\n' $roadmapReplacement -Optional
    Replace-Literal $roadmap '- core v0.4 analysis/reference behavior remains green;' '- core analysis/reference behavior remains green;' -Optional

    $active = Join-Path $Root 'docs\ACTIVE_CURRENT.md'
    $topReplacement = @"
# ACTIVE / CURRENT

Published stable version: **none**

Active development version: **0.5.0.dev0**

Active development scope: **v0.5 CLaMP 3 semantic retrieval**

Epic: **#26**

Current first implementation issue: **#27**

"@
    Replace-Regex $active '(?ms)^# ACTIVE / CURRENT\s+Stable version:.*?Current first implementation issue: \*\*#27\*\*\s*' $topReplacement -Optional
    Replace-Literal $active '## Stable v0.4 implementation' '## Core analysis baseline' -Optional
    Replace-Literal $active 'Genre_test 0.4.0 remains a local Windows-first music profiling and regression system built around:' 'The core analysis baseline remains a local Windows-first music profiling and regression system built around:' -Optional
    Replace-Literal $active 'No v0.5 retrieval work may silently change these outputs without separate review and evidence.' 'Retrieval work may not silently change these outputs without separate review and evidence.' -Optional

    $rus = Join-Path $Root 'README_RUS.md'
    Replace-Literal $rus '## Стабильная база v0.4.0' '## Базовый анализатор' -Optional
    Replace-Literal $rus '## v0.4 — Стабильный анализатор' '## Завершённый этап — базовый анализатор' -Optional
    Replace-Literal $rus 'Статус: **готово и используется как стабильная база**.' 'Статус: **готово; функциональность сохранена в текущей линии разработки**.' -Optional
}

function Update-CI {
    param([Parameter(Mandatory)][string]$Root)

    $ci = Join-Path $Root '.github\workflows\ci.yml'

    $old = @"
          grep -Fq 'Publish v0.4.0 files into repository releases folder' .github/workflows/release-v0.4.0.yml
          grep -Fq 'releases/Genre_test_0.4.0_portable.zip' .github/workflows/release-v0.4.0.yml
          echo '0.3.x active-release legacy retirement gate PASS'
"@
    $new = @"
          test ! -e .github/workflows/release-v0.4.0.yml
          test ! -e RELEASE_NOTES_0.4.0.md
          test ! -e releases/Genre_test_0.4.0_portable.zip
          test ! -e releases/RELEASE_NOTES_0.4.0.md
          echo 'retired release artifact gate PASS'
"@
    Replace-Literal $ci $old $new -Optional

    Replace-Literal $ci "throw 'v0.4 setup does not pin the CUDA 13.0 PyTorch path.'" "throw 'Current setup does not pin the CUDA 13.0 PyTorch path.'" -Optional
    Replace-Literal $ci "throw 'v0.4 release bootstrap does not pin Torch 2.12.1 / cu130 / CPU routes.'" "throw 'Current release bootstrap does not pin Torch 2.12.1 / cu130 / CPU routes.'" -Optional
    Replace-Literal $ci "throw 'v0.4 release bootstrap is missing NVIDIA PnP/native architecture gates.'" "throw 'Current release bootstrap is missing NVIDIA PnP/native architecture gates.'" -Optional
}

function Update-RuntimeDoc {
    param([Parameter(Mandatory)][string]$Root)

    $path = Join-Path $Root 'docs\GPU_RUNTIME.md'
    if (-not (Test-Path -LiteralPath $path)) { return }

    Replace-Literal $path '# Genre_test 0.4 GPU runtime' '# Genre_test GPU runtime' -Optional
    Replace-Literal $path '## Release baseline' '## Runtime baseline' -Optional
    Replace-Literal $path 'Genre_test 0.4 targets the following reproducible Windows GPU runtime:' 'Genre_test targets the following reproducible Windows GPU runtime:' -Optional
    Replace-Literal $path 'because the 0.4 accelerated release target is CUDA 13.0.' 'because the accelerated runtime target is CUDA 13.0.' -Optional
    Replace-Literal $path 'A real Windows Blackwell CUDA smoke remains required before merging v0.4.0.' 'A real Windows Blackwell CUDA smoke remains required before publishing a packaged release.' -Optional

    # Update links after the filename rename.
    $tracked = Invoke-Native git @('-C', $Root, 'ls-files')
    foreach ($rel in ($tracked.Output -split "`n")) {
        if (-not $rel) { continue }
        if ($rel -match '^(legacy/|releases/)' -or $rel -match '\.(zip|pdf|wav|mp3|flac)$') { continue }

        $full = Join-Path $Root $rel
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { continue }

        try {
            $text = Get-Content -LiteralPath $full -Raw -Encoding UTF8
        } catch {
            continue
        }

        if ($text.Contains('GPU_RUNTIME_0.4.md')) {
            $text = $text.Replace('GPU_RUNTIME_0.4.md', 'GPU_RUNTIME.md')
            Set-Content -LiteralPath $full -Value $text -Encoding utf8NoBOM -NoNewline
        }
    }
}

function Update-Tests {
    param([Parameter(Mandatory)][string]$Root)

    $cli = Join-Path $Root 'tests\test_cli_defaults.py'
    if (Test-Path -LiteralPath $cli) {
        Replace-Literal $cli '_assert_v04_defaults' '_assert_defaults' -Optional
        Replace-Literal $cli 'test_v04_analyze_defaults_to_all_views_and_short_paths' 'test_analyze_defaults_to_all_views_and_short_paths' -Optional
        Replace-Literal $cli 'test_v04_batch_defaults_to_all_views_and_short_paths' 'test_batch_defaults_to_all_views_and_short_paths' -Optional
    }

    $profile = Join-Path $Root 'tests\test_profile.py'
    if (Test-Path -LiteralPath $profile) {
        $text = Get-Content -LiteralPath $profile -Raw -Encoding UTF8
        if ($text -notmatch 'from genre_test import __version__') {
            $text = $text.Replace(
                'from dataclasses import replace',
                "from dataclasses import replace`n`nfrom genre_test import __version__"
            )
        }
        $text = $text.Replace('analyzer_version="0.4.0"', 'analyzer_version=__version__')
        Set-Content -LiteralPath $profile -Value $text -Encoding utf8NoBOM -NoNewline
    }

    $releaseTest = Join-Path $Root 'tests\test_release_bootstrap.py'
    if (Test-Path -LiteralPath $releaseTest) {
        Replace-Literal $releaseTest 'test_v04_release_bootstrap_runtime_contract' 'test_release_bootstrap_runtime_contract' -Optional

        $pattern = '(?ms)^def test_portable_docs_are_v04_and_not_fixed_to_old_path\(\) -> None:.*$'
        $replacement = @"
def test_portable_docs_do_not_advertise_retired_release() -> None:
    english = (ROOT / "PORTABLE_README.txt").read_text(encoding="utf-8")
    russian = (ROOT / "README_RU.txt").read_text(encoding="utf-8")

    assert "0.4.0" not in english
    assert "0.4.0" not in russian
    assert "Python 3.11 / 3.12 / 3.13 x64" in english
    assert "Python 3.11 / 3.12 / 3.13 x64" in russian
    assert "PyTorch 2.12.1" in english
    assert "PyTorch 2.12.1" in russian
"@
        Replace-Regex $releaseTest $pattern $replacement -Optional
    }

    $manifestTest = Join-Path $Root 'tests\test_regression_manifest.py'
    Replace-Literal $manifestTest 'regression_cases_v04.json' 'regression_cases.json' -Optional
}

function Write-ReleasesReadme {
    param([Parameter(Mandatory)][string]$Root)

    $content = @"
# Genre_test releases

There is currently **no published stable packaged release**.

Active development version: **0.5.0.dev0**.

The former portable release, its checksum file, release notes, GitHub Release
entry and release tag are retired. Historical source remains available through
Git history.

A future release must be generated by a version-neutral release workflow and
must not push directly to `main`.
"@
    Set-Content -LiteralPath (Join-Path $Root 'releases\README.md') -Value $content -Encoding utf8NoBOM
}

function Prepare-LocalCleanup {
    param([Parameter(Mandatory)][string]$Root)

    Write-Host "Preparing local retirement changes..."

    foreach ($p in @(
        '.github/workflows/release-v0.4.0.yml',
        'RELEASE_NOTES_0.4.0.md',
        'releases/Genre_test_0.4.0_portable.zip',
        'releases/RELEASE_NOTES_0.4.0.md',
        'releases/SHA256SUMS.txt'
    )) {
        Remove-TrackedPath $Root $p
    }

    Move-TrackedPath $Root 'docs/GPU_RUNTIME_0.4.md' 'docs/GPU_RUNTIME.md'
    Move-TrackedPath $Root 'tests/fixtures/regression_cases_v04.json' 'tests/fixtures/regression_cases.json'
    Move-TrackedPath $Root 'tests/test_cli_v04.py' 'tests/test_cli_defaults.py'
    Move-TrackedPath $Root 'tests/test_profile_v04.py' 'tests/test_profile.py'
    Move-TrackedPath $Root 'tests/test_release_bootstrap_v04.py' 'tests/test_release_bootstrap.py'

    Write-GenericPortableDocs $Root
    Write-ReleasesReadme $Root
    Update-CurrentDocs $Root
    Update-CI $Root
    Update-RuntimeDoc $Root
    Update-Tests $Root

    # Neutralize stale version wording in implementation scripts without
    # changing runtime semantics.
    foreach ($rel in @('scripts/setup.ps1','scripts/release_bootstrap.ps1')) {
        $full = Join-Path $Root $rel
        if (Test-Path -LiteralPath $full) {
            $text = Get-Content -LiteralPath $full -Raw -Encoding UTF8
            $text = $text.Replace('v0.4 release', 'current release')
            $text = $text.Replace('v0.4 setup', 'current setup')
            Set-Content -LiteralPath $full -Value $text -Encoding utf8NoBOM -NoNewline
        }
    }

    Invoke-Native git @('-C', $Root, 'add', '-A') | Out-Null
    Invoke-Native git @('-C', $Root, '-c', 'core.whitespace=cr-at-eol', 'diff', '--cached', '--check') | Out-Null

    Write-Host "Local cleanup prepared and staged."
}

function Get-GitHubObject {
    param([Parameter(Mandatory)][string]$Endpoint)

    $r = Invoke-Native gh @(
        'api', $Endpoint,
        '-H', 'X-GitHub-Api-Version: 2026-03-10'
    ) -AllowFailure

    if ($r.ExitCode -ne 0) {
        return $null
    }

    if (-not $r.Output.Trim()) {
        return $null
    }

    return ($r.Output | ConvertFrom-Json)
}

function Remove-GitHubReleaseAndTag {
    Ensure-Gh

    $release = Get-GitHubObject "repos/$Repository/releases/tags/$RetiredTag"
    if ($null -ne $release) {
        Write-Host "Deleting GitHub Release $RetiredTag (id=$($release.id))..."
        Invoke-Native gh @(
            'api', '--method', 'DELETE',
            "repos/$Repository/releases/$($release.id)",
            '-H', 'X-GitHub-Api-Version: 2026-03-10'
        ) | Out-Null
    } else {
        Write-Host "GitHub Release $RetiredTag already absent."
    }

    $tag = Get-GitHubObject "repos/$Repository/git/ref/tags/$RetiredTag"
    if ($null -ne $tag) {
        Write-Host "Deleting Git tag $RetiredTag..."
        Invoke-Native gh @(
            'api', '--method', 'DELETE',
            "repos/$Repository/git/refs/tags/$RetiredTag",
            '-H', 'X-GitHub-Api-Version: 2026-03-10'
        ) | Out-Null
    } else {
        Write-Host "Git tag $RetiredTag already absent."
    }
}

function Check-State {
    param(
        [Parameter(Mandatory)][string]$Root,
        [switch]$RequireGitHubAbsent
    )

    $failed = $false

    Write-Host ""
    Write-Host "=== Local active-tree check ==="

    foreach ($p in @(
        '.github/workflows/release-v0.4.0.yml',
        'RELEASE_NOTES_0.4.0.md',
        'releases/Genre_test_0.4.0_portable.zip',
        'releases/RELEASE_NOTES_0.4.0.md',
        'releases/SHA256SUMS.txt',
        'docs/GPU_RUNTIME_0.4.md',
        'tests/fixtures/regression_cases_v04.json',
        'tests/test_cli_v04.py',
        'tests/test_profile_v04.py',
        'tests/test_release_bootstrap_v04.py'
    )) {
        if (Test-Path -LiteralPath (Join-Path $Root $p)) {
            Write-Host "FAIL stale path exists: $p"
            $failed = $true
        } else {
            Write-Host "PASS absent: $p"
        }
    }

    $required = @(
        'docs/GPU_RUNTIME.md',
        'tests/fixtures/regression_cases.json',
        'tests/test_cli_defaults.py',
        'tests/test_profile.py',
        'tests/test_release_bootstrap.py',
        'releases/README.md'
    )

    foreach ($p in $required) {
        if (Test-Path -LiteralPath (Join-Path $Root $p)) {
            Write-Host "PASS present: $p"
        } else {
            Write-Host "FAIL required path missing: $p"
            $failed = $true
        }
    }

    $checks = @{
        'README.md' = @(
            'Latest stable release: 0.4.0',
            'releases/Genre_test_0.4.0_portable.zip',
            'GitHub Release `v0.4.0`'
        )
        'releases/README.md' = @('Current supported release: **v0.4.0**')
        'docs/ACTIVE_CURRENT.md' = @(
            'Stable version: **0.4.0**',
            'Main release tag: `v0.4.0`'
        )
        'ROADMAP.md' = @('**v0.4.0 — released**')
        'PORTABLE_README.txt' = @('Genre_test 0.4.0')
        'README_RU.txt' = @('Genre_test 0.4.0')
    }

    foreach ($entry in $checks.GetEnumerator()) {
        $path = Join-Path $Root $entry.Key
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        foreach ($needle in $entry.Value) {
            if ($text.Contains($needle)) {
                Write-Host "FAIL stale current-state marker in $($entry.Key): $needle"
                $failed = $true
            }
        }
    }

    if ($RequireGitHubAbsent) {
        Ensure-Gh
        Write-Host ""
        Write-Host "=== GitHub check ==="

        $release = Get-GitHubObject "repos/$Repository/releases/tags/$RetiredTag"
        if ($null -ne $release) {
            Write-Host "FAIL GitHub Release still exists: $RetiredTag"
            $failed = $true
        } else {
            Write-Host "PASS GitHub Release absent: $RetiredTag"
        }

        $tag = Get-GitHubObject "repos/$Repository/git/ref/tags/$RetiredTag"
        if ($null -ne $tag) {
            Write-Host "FAIL Git tag still exists: $RetiredTag"
            $failed = $true
        } else {
            Write-Host "PASS Git tag absent: $RetiredTag"
        }
    }

    if ($failed) {
        Write-Host ""
        Write-Host "RESULT: FAIL"
        return $false
    }

    Write-Host ""
    Write-Host "RESULT: PASS"
    return $true
}

function Wait-ForPrChecks {
    param(
        [Parameter(Mandatory)][string]$PrNumber
    )

    for ($attempt = 1; $attempt -le 18; $attempt++) {
        $probe = Invoke-Native gh @(
            'pr','checks',$PrNumber,
            '--repo',$Repository
        ) -AllowFailure

        if ($probe.ExitCode -eq 0 -or $probe.Output -notmatch '(?i)no checks') {
            break
        }

        Start-Sleep -Seconds 5
    }

    Write-Host "Watching PR #$PrNumber checks..."
    Invoke-Native gh @(
        'pr','checks',$PrNumber,
        '--repo',$Repository,
        '--watch',
        '--fail-fast'
    ) | Out-Null
}

function Run-TargetedTests {
    param([Parameter(Mandatory)][string]$Root)

    if ($SkipTests) {
        Write-Host "Targeted tests skipped by request."
        return
    }

    $python = $null
    foreach ($candidate in @(
        (Join-Path $Root '.venv\Scripts\python.exe'),
        'python'
    )) {
        if ($candidate -eq 'python') {
            if (Get-Command python -ErrorAction SilentlyContinue) {
                $python = 'python'
                break
            }
        } elseif (Test-Path -LiteralPath $candidate) {
            $python = $candidate
            break
        }
    }

    if (-not $python) {
        throw "Python not found. Re-run with -SkipTests only if you intentionally accept that risk."
    }

    Invoke-Native $python @(
        '-m','pytest','-q',
        (Join-Path $Root 'tests\test_cli_defaults.py'),
        (Join-Path $Root 'tests\test_profile.py'),
        (Join-Path $Root 'tests\test_release_bootstrap.py'),
        (Join-Path $Root 'tests\test_regression_manifest.py')
    ) | Out-Null

    Write-Host "Targeted regression tests PASS."
}

$root = Get-RepoRoot
Assert-CorrectRepository $root

switch ($Mode) {
    'Check' {
        Ensure-Gh
        $ok = Check-State $root
        Write-Host ""
        Write-Host "Note: Check mode reports whether the local cleanup is already applied."
        Write-Host "GitHub Release/tag are checked only after FinalizeGitHub or Full."
        if (-not $ok) { exit 2 }
        exit 0
    }

    'Prepare' {
        Assert-CleanWorkingTree $root

        Invoke-Native git @('-C', $root, 'fetch', 'origin', 'main', '--tags') | Out-Null

        $current = (Invoke-Native git @('-C', $root, 'branch', '--show-current')).Output.Trim()
        if ($current -ne $Branch) {
            $exists = Invoke-Native git @('-C', $root, 'show-ref', '--verify', '--quiet', "refs/heads/$Branch") -AllowFailure
            if ($exists.ExitCode -eq 0) {
                throw "Local branch '$Branch' already exists. Switch to it explicitly or delete it before retrying."
            }

            Invoke-Native git @('-C', $root, 'switch', '-c', $Branch, 'origin/main') | Out-Null
        }

        Prepare-LocalCleanup $root
        Run-TargetedTests $root

        Write-Host ""
        Write-Host "Prepared branch: $Branch"
        Write-Host "Review:"
        Write-Host "  git diff --cached"
        Write-Host ""
        Write-Host "Nothing was pushed or deleted from GitHub."
    }

    'FinalizeGitHub' {
        Ensure-Gh

        # Safety: only delete release/tag after main no longer contains the release workflow/artifacts.
        $tree = Invoke-Native gh @(
            'api',
            "repos/$Repository/git/trees/main?recursive=1",
            '--jq',
            '.tree[].path'
        )

        $remotePaths = $tree.Output -split "`n"
        foreach ($blocked in @(
            '.github/workflows/release-v0.4.0.yml',
            'RELEASE_NOTES_0.4.0.md',
            'releases/Genre_test_0.4.0_portable.zip',
            'releases/RELEASE_NOTES_0.4.0.md'
        )) {
            if ($remotePaths -contains $blocked) {
                throw "Refusing GitHub deletion: main still contains '$blocked'. Merge the cleanup PR first."
            }
        }

        Remove-GitHubReleaseAndTag

        $ok = Check-State $root -RequireGitHubAbsent
        if (-not $ok) { exit 2 }
    }

    'Full' {
        Ensure-Gh
        Assert-CleanWorkingTree $root

        # Apply non-Pro repository governance first.
        & (Join-Path $PSScriptRoot 'install-repo-guards.ps1')
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        & (Join-Path $PSScriptRoot 'github-settings.ps1') -Mode Apply -InstallGh:$InstallGh
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Invoke-Native git @('-C', $root, 'fetch', 'origin', 'main', '--tags') | Out-Null

        $current = (Invoke-Native git @('-C', $root, 'branch', '--show-current')).Output.Trim()
        if ($current -ne $Branch) {
            $exists = Invoke-Native git @('-C', $root, 'show-ref', '--verify', '--quiet', "refs/heads/$Branch") -AllowFailure
            if ($exists.ExitCode -eq 0) {
                throw "Local branch '$Branch' already exists. Resolve it before Full mode."
            }
            Invoke-Native git @('-C', $root, 'switch', '-c', $Branch, 'origin/main') | Out-Null
        }

        Prepare-LocalCleanup $root
        Run-TargetedTests $root

        $cached = Invoke-Native git @('-C', $root, 'diff', '--cached', '--quiet') -AllowFailure
        if ($cached.ExitCode -eq 0) {
            throw "No cleanup changes were produced."
        }

        Invoke-Native git @(
            '-C', $root,
            'commit', '-m', 'chore: retire v0.4 release artifacts'
        ) | Out-Null

        Invoke-Native git @('-C', $root, 'push', '-u', 'origin', $Branch) | Out-Null

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

- retire the old packaged release workflow and repository release artifacts;
- keep current regression coverage but remove version-specific v04 test names;
- make current docs consistent with the active 0.5.0.dev0 development line;
- preserve version-neutral packaged bootstrap support;
- install settings-as-code / local main push guard separately from GitHub Pro features.

## GitHub finalization

After CI passes and this PR is merged, the local orchestrator deletes:
- GitHub Release v0.4.0
- Git tag v0.4.0

No direct push to main is used.
"@

            $created = Invoke-Native gh @(
                'pr','create',
                '--repo',$Repository,
                '--base','main',
                '--head',$Branch,
                '--title','chore: retire v0.4 release artifacts',
                '--body',$body
            )
            Write-Host $created.Output

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

        Wait-ForPrChecks -PrNumber $prNumber

        Write-Host "CI passed. Squash-merging PR #$prNumber..."
        Invoke-Native gh @(
            'pr','merge',$prNumber,
            '--repo',$Repository,
            '--squash',
            '--delete-branch'
        ) | Out-Null

        Invoke-Native git @('-C', $root, 'switch', 'main') | Out-Null
        Invoke-Native git @('-C', $root, 'pull', '--ff-only', 'origin', 'main') | Out-Null

        $localBranch = Invoke-Native git @(
            '-C', $root, 'show-ref', '--verify', '--quiet', "refs/heads/$Branch"
        ) -AllowFailure
        if ($localBranch.ExitCode -eq 0) {
            Invoke-Native git @('-C', $root, 'branch', '-D', $Branch) | Out-Null
        }

        Remove-GitHubReleaseAndTag

        $ok = Check-State $root -RequireGitHubAbsent
        if (-not $ok) { exit 2 }

        Write-Host ""
        Write-Host "FULL RETIREMENT COMPLETE."
    }
}
