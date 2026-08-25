# ACTIVE / CURRENT

Version: **0.4.0**
Status: **released**
Main release tag: `v0.4.0`

## Current implementation

Genre_test 0.4.0 is a local Windows-first music profiling and regression system built around:

```text
Audio
  -> MAEST Discogs519 fine-style evidence
  -> AudioSet AST semantic evidence
  -> BPM / key / source metadata
  -> deterministic profile fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor views
  -> history / Validation / build comparison
```

## Runtime baseline

- Python 3.11 / 3.12 / 3.13 x64
- PyTorch 2.12.1
- NVIDIA: CUDA 13.0 / cu130
- Blackwell requires native active architecture; RTX 5070 Ti `sm_120` verified
- CPU-only mode supported; GUI reports `CUDA: N/A | GPU: N/A`
- NVIDIA present but unusable CUDA is a runtime failure, not CPU fallback
- FFmpeg bootstrap and diagnostics included
- public pinned Hugging Face models work anonymously; token is optional

## Product behavior

- default output view: `all`
- optional full source path
- live Device / mode / view / path switching between tracks
- Safe Stop for Analysis and Validation
- dark theme by default with live Dark / Light switching
- Expert mode exposes MAEST windows and Top-K
- CPU-only UI does not offer CUDA
- History and log paths are clickable

## AudioProfile

- MAEST remains the fine-style classifier
- pinned MIT AudioSet AST provides independent semantic evidence
- genre/family reconciliation prevents contradictory published profiles
- weak AST family evidence keeps absolute confidence and cannot receive a full semantic vote merely because it is the only mapped tag
- semantic failure in `auto` mode falls back to MAEST-only

## Tempo and metadata

- tempo-v2 handles half/double and short-loop 3:2 ambiguity
- source sample rate / bit depth / channels / bitrate are reported from the original file, not the internal 16 kHz model stream
- known short 3:2 test material is tracked separately from independent BPM ground truth

## Validation / history

Default working-copy paths:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\results\
```

Current history identity includes:

- analyzer version
- Git commit
- schema version
- model id / revision
- analysis mode
- run id / timestamp

GUI tabs are separated into:

- **Анализ** — ordinary AudioProfile analysis
- **Validation** — convergence and history drift recheck
- **Проверка** — saved-build comparison / repeatability without re-analyzing audio

Build comparison performs a coverage preflight and refuses meaningless 0-track percentage reports.

Validation output uses explicit `DRIFT: STABLE/MINOR/SIGNIFICANT/CRITICAL` terminology so drift stability is not confused with classifier confidence.

## Release packaging

Current package:

```text
releases\Genre_test_0.4.0_portable.zip
releases\SHA256SUMS.txt
```

The same package is published in GitHub Release `v0.4.0`.

Packaged startup uses only:

```text
Genre_test_START.cmd
scripts\release_bootstrap.ps1
```

The active repository no longer carries 0.3.x portable bootstrap/workflow semantics.

## Accepted release evidence

- Windows Auto catalog run: 25/25 complete, semantic 25/25, file errors 0
- Accurate Validation: 25/25, file errors 0
- Safe Stop verified
- GPU runtime health verified on RTX 5070 Ti
- CI: Python 3.11 / 3.12 / 3.13, Ruff, pytest, launcher and PowerShell/CUDA gates

## Current known development items

- shared audio decode/cache between MAEST and AST
- persistent semantic cache by content/build identity
- explicit genre-ambiguity presentation when Top-1 / Top-2 are nearly tied
- independent BPM ground-truth corpus
- classical resolver/calibration
- larger reviewed benchmark and confusion analysis
- similarity / XLSX / richer calibrated descriptors

Validation measures reproducibility and drift. It does not by itself prove genre correctness; independent/manual labels remain necessary for accuracy claims.
