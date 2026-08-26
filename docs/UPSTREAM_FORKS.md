# Upstream forks for Genre_test development

Tracking issue: #47

The GitHub connector currently used for project automation does not expose a repository-fork/create operation. Create the forks once with GitHub CLI, then all normal branch/file/PR work can continue through the connector.

## One-time fork commands

Run from PowerShell:

```powershell
cd C:\GIT

gh auth status

gh repo fork GeekatplayStudio/music-suite `
  --org rassvetpublic-spec `
  --fork-name music-suite `
  --clone `
  --remote

gh repo fork GeekatplayStudio/ComfyUI-MusicMapper-nodes `
  --org rassvetpublic-spec `
  --fork-name ComfyUI-MusicMapper-nodes `
  --clone `
  --remote
```

Expected GitHub repositories:

```text
rassvetpublic-spec/music-suite
rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

Expected local checkouts:

```text
C:\GIT\music-suite
C:\GIT\ComfyUI-MusicMapper-nodes
```

## Normalize remotes

GitHub CLI normally creates suitable remotes, but verify:

```powershell
cd C:\GIT\music-suite
git remote -v

cd C:\GIT\ComfyUI-MusicMapper-nodes
git remote -v
```

Desired semantic roles:

```text
origin    -> rassvetpublic-spec/<fork>
upstream  -> GeekatplayStudio/<source>
```

If `upstream` is missing:

```powershell
cd C:\GIT\music-suite
git remote add upstream https://github.com/GeekatplayStudio/music-suite.git

cd C:\GIT\ComfyUI-MusicMapper-nodes
git remote add upstream https://github.com/GeekatplayStudio/ComfyUI-MusicMapper-nodes.git
```

## Pin the snapshots inspected by Genre_test

```text
music-suite:
8534963ccafa37dc23df84c6ac239132fba77d41

ComfyUI-MusicMapper-nodes:
0fda892fddfbaf50ba384c34f2b2d73c68d64208
```

Verify locally:

```powershell
cd C:\GIT\music-suite
git fetch upstream
git cat-file -t 8534963ccafa37dc23df84c6ac239132fba77d41

cd C:\GIT\ComfyUI-MusicMapper-nodes
git fetch upstream
git cat-file -t 0fda892fddfbaf50ba384c34f2b2d73c68d64208
```

## Sync policy

Before starting an integration batch:

```powershell
git fetch upstream --prune
git log --oneline --decorate -10 upstream/main
```

Do not silently move a Genre_test dependency from one upstream revision to another. Update the pinned SHA, provenance document and regression evidence in the same PR.

## License boundary

### music-suite

MIT. Preserve the upstream copyright and MIT permission notice in copied or substantial portions.

### ComfyUI-MusicMapper-nodes

At the inspected snapshot GitHub reports no recognized license and no root `LICENSE` file was found. Keep the fork for testing/tracking, but do not copy/relicense substantial source into Genre_test until the upstream license is clarified.
