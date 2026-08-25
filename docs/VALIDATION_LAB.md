# VALIDATION LAB — v0.4.0

## Purpose

Validation Lab checks reproducibility, mode convergence and build-to-build drift. It is deliberately separate from ordinary AudioProfile output.

It answers:

1. Do `Fast`, `Auto` and `Accurate` converge on the same track?
2. Did a new build change a previously stored result?
3. Which tracks need manual review?
4. Are two runs of the same build repeatable?

Validation is not a ground-truth accuracy test. A stable result can still be wrong.

## Track identity

Tracks are identified by SHA-256 content identity:

```text
track_id = sha256:<hex digest>
```

Duplicate byte-identical files at different paths collapse to one logical track during Validation scanning.

## Build identity

Saved comparisons use a composite build identity rather than analyzer semver alone:

- analyzer version
- Git commit
- schema version
- model id
- model revision

This prevents two different `0.4.0` development builds from being treated as identical.

## Local history

Working-copy default:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
```

The database is local and gitignored.

Core history includes tracks, file locations, immutable runs, style/broad evidence, validation sessions and comparisons.

## GUI separation

The Runtime Health GUI uses three independent tabs:

### Анализ

Ordinary MAEST + AudioSet AST AudioProfile analysis and Normal / SUNO / Distributor presentation.

### Validation

Re-analyzes selected files or folders to measure current convergence and history drift.

Modes:

- Быстрый / Fast
- Авто / Auto
- Точный / Accurate
- Fast + Auto + Accurate comparison

Filters:

- all
- stale/missing build results
- unstable

Safe Stop is cooperative: completed results remain stored and the report records the remaining count.

### Проверка

Compares already saved builds without decoding/re-analyzing audio.

The preflight reports:

```text
Build A coverage
Build B coverage
Common tracks
```

If common coverage is zero, comparison stops instead of printing meaningless `0%` metrics.

A repeatability mode compares two saved runs from the same build.

## Drift terminology

Validation labels explicitly describe drift:

```text
DRIFT: STABLE
DRIFT: MINOR
DRIFT: SIGNIFICANT
DRIFT: CRITICAL
```

This is separate from classifier confidence such as `high`, `medium` or `low-medium`.

## Comparison signals

The comparator may use:

- resolved fine-style equality
- broad-family equality
- primary/hybrid classification equality
- broad-distribution Jensen-Shannon divergence
- broad-distribution cosine similarity
- weighted Top-N style overlap
- tempo equivalence
- key/mode equality when both are available

Tempo comparison treats close half/double relationships as equivalent where appropriate. Tempo-v2 itself additionally handles the short-loop 3:2 case in ordinary analysis.

## Large-catalog workflow

For a full local v0.4 regression use:

```powershell
.\scripts\run_large_regression.ps1 -Source "D:\Music" -CompareModes
```

The script runs runtime diagnostics, full ensemble batch analysis and Validation into a timestamped result folder.

For a faster first pass omit `-CompareModes`.

## CLI examples

Full ordinary ensemble batch:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music" --device auto --mode auto --semantic auto --view all
```

Validation of one or more roots:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" "E:\Archive" --filter all
```

Full Fast / Auto / Accurate convergence:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --compare-modes --filter all
```

Only unstable items:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter unstable
```

Historical JSON import remains supported as a migration/data-recovery feature; it is not part of the active release bootstrap architecture.

## Interpretation rule

History and convergence measure consistency, not objective genre correctness. Accuracy calibration requires independently reviewed expected labels, especially for ambiguous fine styles and BPM octave/ratio cases.
