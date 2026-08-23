# ACTIVE / CURRENT

Version: **0.3.2**

## Current implementation

- Windows-first local genre analyzer
- MAEST Discogs 519 via Transformers/PyTorch
- CUDA auto-detection
- `Auto`, `Fast`, `Accurate`, `Expert` analysis modes
- duration-aware adaptive 30-second windows
- resolver with broad/fine-style evidence, hybrid detection and confidence
- BPM/key/basic spectral features
- CLI + Windows GUI
- Validation Lab with multi-root scanning and version history
- cooperative Safe Stop
- repo-local SQLite/history/log/model cache
- persistent validation reports

## v0.3.2 validation hardening

### Resolver

When the broad-family winner disagrees with the strongest fine-style evidence, the resolver no longer keeps a weaker fine style and reports a negative `style_margin`.

Instead it:

- resolves to the strongest fine style from the two leading broad families;
- marks the result `hybrid`;
- keeps confidence at `low-medium`;
- exposes the competing style as `secondary_style`.

This specifically covers real cases such as the v0.3.1 `За хутором` result where broad `Pop` led, while `Rock---Pop Rock` was stronger than `Pop---Ballad`.

### Input QC

```text
< 10 s   -> INSUFFICIENT_AUDIO, no genre verdict
10-30 s  -> SHORT_INPUT, one padded MAEST window, confidence <= medium
>= 30 s  -> NORMAL
```

Every new result records `input_quality` and `quality_notes`. Result schema is now **3**.

### Scanner hygiene

Recursive directory scans ignore these service/runtime locations by default:

```text
.git
.venv
.genre_test
results
__pycache__
Resources/audioAlg
```

Directly selected files are still analyzed even when they live under an ignored directory. CLI provides `--include-service-dirs`, and the Validation GUI has `Игнорировать служебные каталоги` enabled by default.

### Validation reporting

Overall severity is now decomposed into two independent channels:

- **Mode convergence** — Fast vs Auto vs Accurate in the current run
- **History drift** — current result vs previous stored result/version

Reports include:

- mode severity
- worst mode pair
- mode reason
- history severity/reason
- Fast/Auto/Accurate window counts
- Auto vs Accurate resolved-genre match %
- Fast vs Accurate resolved-genre match %
- total/percentage of inference windows saved by Auto
- Auto early-stop count
- input QC counts

### Decoder diagnostics

`genre-test doctor` now reports:

- SoundFile version
- FFmpeg path or `MISSING`
- AAC/extended decode fallback availability
- pinned MAEST model and revision

### Reproducibility

Default model:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
```

Pinned Hugging Face revision:

```text
6c35f32a350f74351870937d5ae0bae1d898d1df
```

New default-model runs therefore no longer store `model_revision: null`.

## Real-data baseline — 2026-08-23

Full catalog convergence run under v0.3.1:

```text
Paths originally found: 291
Unique SHA-256 tracks scanned: 241
Analyzed successfully: 225
Decode errors skipped: 16
Duplicate paths: 50
Remaining: 0

STABLE: 173
MINOR: 25
SIGNIFICANT: 27
CRITICAL: 0

Auto == Accurate resolved genre: 225 / 225 = 100.0%
Fast == Accurate resolved genre: 181 / 225 = 80.4%
```

Interpretation: v0.3.1 Auto policy is accepted as the default working mode. v0.3.2 should be validated primarily against unstable/changed tracks rather than rerunning the whole catalog in triple mode immediately.

## Identity / history

- SHA-256 `track_id` independent of filename/path
- duplicate-content detection across different directories/disks
- path/size/mtime cache to avoid unnecessary rehashing
- repo-local SQLite database by default
- immutable versioned run JSON snapshots
- legacy `*.genre*.json` import when original audio can be resolved

Default Windows data:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\.genre_test\huggingface\
C:\GIT\Genre_test\results\
```

## Important limitation

Validation measures reproducibility and drift. It does not prove genre correctness. Manual/ground-truth genre labels remain necessary for accuracy calibration.
