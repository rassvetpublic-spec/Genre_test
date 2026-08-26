# Upstream forks for Genre_test development

Tracking issue: #47 — completed.

## Current fork state

Created forks:

```text
rassvetpublic-spec/music-suite
rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

Expected local checkouts:

```text
C:\GIT\music-suite
C:\GIT\ComfyUI-MusicMapper-nodes
```

Git remote roles:

```text
origin    -> rassvetpublic-spec/<fork>
upstream  -> GeekatplayStudio/<source>
```

The forks were created with GitHub CLI. When a repository argument is supplied to `gh repo fork`, do **not** add `--remote`; `gh` creates `origin`/`upstream` during the clone flow.

If recreating a fork in the future under the current user account, the working form is:

```powershell
cd C:\GIT

gh repo fork GeekatplayStudio/music-suite --fork-name music-suite --clone

gh repo fork GeekatplayStudio/ComfyUI-MusicMapper-nodes --fork-name ComfyUI-MusicMapper-nodes --clone
```

After clone, make the user-owned fork the GitHub CLI default so `gh pr` / `gh issue` cannot accidentally target upstream:

```powershell
cd C:\GIT\music-suite
gh repo set-default rassvetpublic-spec/music-suite

cd C:\GIT\ComfyUI-MusicMapper-nodes
gh repo set-default rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

Verify remotes:

```powershell
cd C:\GIT\music-suite
git remote -v

cd C:\GIT\ComfyUI-MusicMapper-nodes
git remote -v
```

## Pinned snapshots inspected by Genre_test

```text
music-suite:
8534963ccafa37dc23df84c6ac239132fba77d41

ComfyUI-MusicMapper-nodes:
0fda892fddfbaf50ba384c34f2b2d73c68d64208
```

Before a new integration batch:

```powershell
git fetch upstream --prune
git log --oneline --decorate -10 upstream/main
```

Do not silently move a Genre_test dependency/reference from one upstream revision to another. Update the pinned SHA, provenance note and regression evidence together.

## License / permission boundary

### `music-suite`

Published MIT license. Preserve the upstream copyright and MIT permission notice in copied or substantial portions.

### `ComfyUI-MusicMapper-nodes`

At the inspected snapshot GitHub reports no recognized license and no root `LICENSE` file was found.

However, the Genre_test project owner reports **direct written permission from the upstream author to use the repository for non-commercial purposes**. This permission was confirmed in private correspondence with the author.

Project interpretation:

- non-commercial local research, experimentation and integration are permitted under that direct authorization;
- keep upstream attribution and pinned provenance;
- do not represent the repository as MIT/Apache/GPL or another standard OSS license that upstream did not publish;
- do not assume commercial-use rights;
- do not relicense upstream source;
- substantial public redistribution outside the normal GitHub fork relationship should retain a permission note and, if it becomes material, should be backed by an archived copy of the correspondence or a clearer written grant covering redistribution.

The private correspondence itself is **not stored in this repository** unless the project owner explicitly chooses to add/redact it later.

## Sync policy

- preserve upstream history;
- keep `upstream` pointing to GeekatplayStudio;
- do not rewrite upstream history;
- pin upstream SHA before every integration batch;
- experimental changes go through feature branches/PRs;
- Genre_test depends on versioned contracts/artifacts, never an unpinned moving fork `main`;
- all code/model reuse still passes per-dependency provenance checks;
- no merge to Genre_test `main` without explicit MTD.
