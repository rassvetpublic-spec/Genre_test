# ACTIVE / CURRENT

Version: **0.4.0**
Release: **stable**
Primary branch: **main**

## Current product state

Genre_test 0.4.0 is the active supported line.

Active runtime:

- MAEST Discogs519 detailed genre/style classifier;
- pinned AudioSet AST semantic classifier;
- AudioProfile schema 4;
- Normal / SUNO / Distributor presentation;
- BPM/key/source metadata;
- build-aware SQLite history;
- separate Analysis / Validation / Проверка GUI tabs;
- dark theme by default with live Dark/Light switching;
- Safe Stop and live mode/view/path/device controls;
- Python 3.11/3.12/3.13 x64;
- PyTorch 2.12.1;
- NVIDIA CUDA 13.0 / cu130;
- Blackwell native architecture gate, including sm_120;
- CPU-only fallback with CUDA/GPU reported as N/A;
- WinGet / VC++ / FFmpeg / Python / .venv bootstrap;
- packaged portable release via scripts/release_bootstrap.ps1.

## Supported launch paths

Working Git checkout:

```text
C:\GIT\Genre_test\Genre_test_START.cmd
```

Portable release:

```text
Genre_test_0.4.0_portable\Genre_test_START.cmd
```

The active launcher has no legacy 0.3.x portable fallback.

## Models

MAEST:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
revision: 6c35f32a350f74351870937d5ae0bae1d898d1df
```

AudioSet AST:

```text
MIT/ast-finetuned-audioset-10-10-0.4593
revision: f826b80d28226b62986cc218e5cec390b1096902
```

## Validation contract

Validation separates:

- mode convergence;
- history drift;
- build-to-build comparison;
- repeatability of the same build.

`DRIFT: STABLE` means no meaningful drift relative to history/mode; it does not mean genre confidence is high.

Build identity includes analyzer version, git commit, schema and model revision.

## Regression evidence for v0.4.0 release

Windows GPU release candidate:

```text
Auto batch: 25 / 25 complete
Semantic profiles: 25 / 25
File errors: 0
Runtime: Deps 12/12 | CUDA OK | GPU OK | FFmpeg OK | HF OK
```

Safe Stop, live settings, dark/light theme, build comparison preflight and CPU-only device handling were smoke-tested during the v0.4 cycle.

## Known development items

- Top-1 / Top-2 ambiguity calibration for short or near-tied tracks;
- independent ground-truth BPM labels for registered tempo ambiguity cases;
- xLaunge mode-convergence case;
- shared audio decode/cache between MAEST and AST;
- Classical period/style resolver;
- XLSX catalog export and musical similarity;
- larger manually reviewed ground-truth corpus.

## Runtime data

Working checkout defaults:

```text
.genre_test\history.sqlite3
.genre_test\logs\genre_test.log
results\
```

History import can read older snapshots for regression purposes. This is data compatibility only; old portable runtimes are not part of the active product.

## Large-corpus regression

```powershell
.\scripts\run-large-regression.ps1 -Source "D:\Music\BASE"
```

Full Fast + Auto + Accurate convergence:

```powershell
.\scripts\run-large-regression.ps1 -Source "D:\Music\BASE" -FullValidation
```

## Release location

Current release is published both as GitHub Release `v0.4.0` and in the repository `releases/` directory.
