# Genre_test — Governance + v0.4 retirement package

Target repository:

`rassvetpublic-spec/Genre_test`

Assumptions:

- private repository;
- GitHub Pro is unavailable;
- Windows + PowerShell 7;
- desired workflow: branch → PR → CI → squash merge;
- no direct push to `main`.

## What this package does

### Repository settings as code

Canonical desired state:

`config/github/settings.json`

Managed repository settings:

- default branch `main`;
- Issues on;
- Projects on;
- Wiki off;
- Discussions off;
- squash merge on;
- merge commits off;
- rebase merge off;
- auto-merge off;
- delete branch after merge on;
- allow PR branch update on.

Managed Actions policy:

- Actions enabled;
- GitHub-owned Actions only;
- default `GITHUB_TOKEN` is read-only;
- workflows cannot approve pull requests by default.

### Local `main` guard

`.githooks/pre-push` blocks accidental local pushes to `refs/heads/main`.

This is a local safety layer, not server-side GitHub branch protection.

### Retires the old v0.4 packaged release

The cleanup PR removes:

- `.github/workflows/release-v0.4.0.yml`;
- `RELEASE_NOTES_0.4.0.md`;
- `releases/Genre_test_0.4.0_portable.zip`;
- `releases/RELEASE_NOTES_0.4.0.md`;
- obsolete `releases/SHA256SUMS.txt`.

It also:

- rewrites `releases/README.md` so it no longer advertises v0.4 as current;
- makes the main README/ROADMAP/ACTIVE_CURRENT consistent with `0.5.0.dev0`;
- renames `docs/GPU_RUNTIME_0.4.md` to `docs/GPU_RUNTIME.md`;
- preserves regression tests while removing version-specific `*_v04` filenames;
- renames `regression_cases_v04.json` to `regression_cases.json`;
- updates CI so it no longer requires the retired release workflow.

### Deletes v0.4 from GitHub after merge

Only after the cleanup PR passes CI and is merged, Full mode deletes:

- GitHub Release `v0.4.0`;
- Git tag `v0.4.0`.

Deleting the Release also removes its Release assets.

Git history is intentionally not rewritten. Historical commits remain recoverable.

## Important sequencing

The GitHub Release/tag are deleted **after** the cleanup PR is merged.

This prevents the old workflow still present on `main` from recreating the retired release.

## Install

Extract this ZIP directly into:

`C:\GIT\Genre_test`

The package adds new governance scripts/config and does not intentionally overwrite application code on extraction.

## 1. Check only

No changes:

```powershell
pwsh .\scripts\repo-governance.ps1 -Mode Check
```

or:

`CHECK_GOVERNANCE.cmd`

Before retirement this is expected to report FAIL for the old v0.4 artifacts.

## 2. Prepare only

Applies GitHub settings, installs the local push guard, creates:

`chore/retire-v0.4`

and stages the cleanup diff.

It does **not** push, open a PR, merge, or delete the GitHub Release/tag.

```powershell
pwsh .\scripts\repo-governance.ps1 -Mode Prepare -InstallGh
```

or:

`PREPARE_GOVERNANCE_AND_RETIRE_V04.cmd`

Review:

```powershell
git diff --cached
```

## 3. Full automatic workflow

```powershell
pwsh .\scripts\repo-governance.ps1 -Mode Full -InstallGh
```

or:

`FULL_GOVERNANCE_AND_RETIRE_V04.cmd`

Full mode performs:

1. validate clean working tree;
2. install local `main` guard;
3. apply repository settings through GitHub API;
4. create cleanup branch from `origin/main`;
5. prepare v0.4 retirement changes;
6. run targeted regression tests;
7. commit;
8. push only the cleanup branch;
9. create PR;
10. watch PR CI;
11. squash merge only after CI passes;
12. update local `main`;
13. delete GitHub Release `v0.4.0`;
14. delete Git tag `v0.4.0`;
15. verify local active tree + GitHub state.

## Authentication

If GitHub CLI is not installed, `-InstallGh` installs it through WinGet.

If it is not authenticated, run once:

```powershell
gh auth login
```

Then re-run the package.

No PAT/API token is stored in this package.

## Safety properties

- refuses to mix cleanup with a dirty working tree;
- verifies `origin` is the expected Genre_test repository;
- never pushes directly to `main`;
- does not delete the GitHub Release/tag before the cleanup is merged;
- does not rewrite Git history;
- preserves useful regression coverage instead of deleting tests merely because their names contained `v04`;
- `Check` mode is read-only;
- `Prepare` mode stops before remote write/merge;
- `Full` mode stops if CI fails.

## Current GitHub state this package was built against

At package creation time:

- development version: `0.5.0.dev0`;
- GitHub Release `v0.4.0` exists;
- Git tag `v0.4.0` exists;
- old release workflow exists and writes directly to `main`;
- repository tree still contains the old portable ZIP and release notes.

The package is designed to retire that state without losing Git history.

## Compatibility note

`has_downloads` is intentionally not managed because the current GitHub repository API response for this private repository does not expose that property reliably. It must not block governance verification.
