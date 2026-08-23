# ACTIVE / CURRENT

Version: **0.3.0**

## Current implementation

- Windows-first local genre analyzer
- MAEST Discogs 519 via Transformers/PyTorch
- CUDA auto-detection
- `Auto`, `Fast`, `Accurate`, `Expert` analysis modes
- duration-aware adaptive 30-second windows
- resolver with broad/fine-style evidence, hybrid detection and confidence
- BPM/key/basic spectral features
- CLI + Windows GUI
- **Validation Lab** with multi-root scanning and version history

## v0.3 Validation Lab

### Identity / history

- SHA-256 `track_id` independent of filename/path
- duplicate-content detection across different directories/disks
- path/size/mtime cache to avoid unnecessary rehashing
- local SQLite database outside the repo by default
- immutable versioned run JSON snapshots
- legacy `*.genre*.json` import when original audio can be resolved

Every v0.3 run records:

- `schema_version`
- `analyzer_version`
- `run_id`
- `analyzed_at`
- `track_id`
- `analysis_mode`
- `windows_analyzed`
- `window_seconds`
- `internal_top_k`
- `report_top_k`
- model/revision/device
- Git commit when available

### Convergence / drift

Validation can run Fast + Auto + Accurate from one shared prediction cache and automatically compare:

- broad family
- resolved genre
- primary/hybrid classification
- Jensen-Shannon divergence
- cosine similarity
- weighted Top-N style overlap
- BPM including half/double-time equivalence
- key/mode

Severity:

```text
STABLE
MINOR
SIGNIFICANT
CRITICAL
```

Mode convergence:

```text
HIGH / MEDIUM / LOW / FAIL
```

### Recheck filters

- all tracks
- only results from older analyzer versions
- only unstable tracks

### Version comparison

Stored analyzer versions can be compared globally with per-track rows and aggregate metrics:

- resolved genre match %
- broad family match %
- tempo-equivalent %
- key/mode match %
- severity counts

## GUI

Tabs:

```text
Анализ
Validation / Перепроверка
```

Validation tab supports multiple folders/files, history DB selection, recheck filters, Fast/Auto/Accurate convergence, legacy JSON import and analyzer-version comparison.

## History location

Default Windows location:

```text
%LOCALAPPDATA%\Genre_test\history.sqlite3
```

SQLite/history data is local and gitignored.

## Validation status

- previous 11-track diagnostic set remains useful as legacy evidence
- new pure tests cover content identity, history, drift severity, tempo equivalence, convergence and recheck policy
- old JSON can be imported into v0.3 history
- next real-data gate is to rerun the catalog under v0.3 and compare Auto ↔ Accurate convergence

## Important limitation

Validation measures reproducibility and drift. It does not prove genre correctness. Manual/ground-truth genre labels remain necessary for accuracy calibration.
