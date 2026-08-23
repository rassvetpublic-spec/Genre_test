# VALIDATION LAB — v0.3.0

## Purpose

Validation Lab turns Genre_test from a one-shot classifier into a versioned test system. It is designed to answer three questions:

1. Do `Fast`, `Auto` and `Accurate` converge on the same track?
2. Did a Genre_test update change a previously stored result?
3. Which tracks need manual review because the disagreement is material?

## Track identity

Tracks are identified by SHA-256 of file contents:

```text
track_id = sha256:<hex digest>
```

A file can move between disks or folders and still resolve to the same track. Identical duplicate files at different paths collapse to one logical track during Validation scans.

The SQLite `file_locations` cache stores path + size + mtime so unchanged files do not need to be rehashed on every scan.

## Local history database

Default path:

```text
Windows: %LOCALAPPDATA%\Genre_test\history.sqlite3
Linux:   $XDG_DATA_HOME/Genre_test/history.sqlite3
         or ~/.local/share/Genre_test/history.sqlite3
```

The database is local and gitignored.

Core tables:

- `tracks` — logical content identities
- `file_locations` — current/previous filesystem locations
- `runs` — complete versioned analysis runs
- `style_scores` — detailed MAEST style scores
- `broad_scores` — broad-family scores
- `validation_sessions` — recheck sessions
- `comparisons` — mode/version/rerun comparisons

## Immutable run metadata

Every v0.3 result stores:

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
- `model_id`
- `model_revision`
- `device`
- `git_commit` when available

Result JSON filenames include analyzer version, mode and run-id prefix, so a new analysis does not overwrite the previous run snapshot.

## Multi-mode convergence

`Fast + Auto + Accurate` uses one decoded track and one shared prediction cache. The analyzer computes only the window predictions needed by the union of the requested modes.

Pairwise comparisons are produced for:

- Fast vs Auto
- Fast vs Accurate
- Auto vs Accurate

Overall convergence:

| Worst pairwise severity | Convergence |
|---|---|
| STABLE | HIGH |
| MINOR | MEDIUM |
| SIGNIFICANT | LOW |
| CRITICAL | FAIL |

## Drift metrics

The comparator does not rely on the final genre string alone. It checks:

- broad-family equality
- resolved fine-style equality
- primary/hybrid classification equality
- normalized broad-distribution Jensen-Shannon divergence
- broad-distribution cosine similarity
- rank-weighted Top-N detailed-style overlap
- BPM equivalence
- key/mode equality when both are known

### Tempo equivalence

The following are treated as equivalent tempo interpretations within tolerance:

```text
x
x / 2
x * 2
```

Therefore `81.5 BPM` vs `163 BPM` is reported as `half-double`, not as a large tempo disagreement.

## Severity

### STABLE

Genre evidence is convergent and only small numerical drift is present.

### MINOR

Typical cases:

- fine style changes while broad family remains the same
- moderate probability drift
- key/mode changes
- detailed Top-N overlap falls substantially

### SIGNIFICANT

Typical cases:

- broad family changes without a high-confidence contradiction
- `primary` ↔ `hybrid` changes
- large probability-distribution drift
- BPM is neither close nor half/double equivalent

### CRITICAL

Typical cases:

- two high-confidence runs disagree on broad family
- extremely large broad-distribution drift

Thresholds are diagnostic defaults and remain subject to benchmark calibration.

## Recheck filters

Validation supports:

- `all` — analyze all discovered tracks
- `old_versions` — analyze only tracks whose latest relevant run is not from the current analyzer version
- `unstable` — analyze tracks with non-high confidence, hybrid classification, or a latest SIGNIFICANT/CRITICAL comparison

## Scattered catalogs

GUI Validation accepts multiple roots and individual files, for example:

```text
D:\Документы\! SUNO
E:\Music Archive
F:\Old Releases
D:\single_track.mp3
```

All sources are scanned recursively and deduplicated by content hash.

## Legacy JSON import

Existing `*.genre*.json` can be imported into history.

If the JSON has no `track_id`, the original audio path from its `path` field must still resolve so Genre_test can compute SHA-256 and associate the historical result with the correct logical track.

Legacy JSON without analyzer metadata is stored as `legacy-unknown`. Import IDs are deterministic for the same unchanged JSON file to prevent duplicate imports.

## GUI

The second tab is:

```text
Validation / Перепроверка
```

It provides:

- multiple source roots/files
- local history DB selection
- `all / old versions / unstable` filters
- `Auto / Fast / Accurate / Fast+Auto+Accurate`
- JSON history import
- version A ↔ version B comparison
- generated validation JSON/CSV reports

## CLI

Recheck one or more roots:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" "E:\Archive" --compare-modes
```

Only old analyzer results:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter old_versions
```

Only unstable tracks:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter unstable
```

Import old JSON:

```powershell
.\.venv\Scripts\genre-test.exe history-import ".\results" "D:\OldGenreResults"
```

Compare two analyzer versions regardless of stored analysis mode:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.2.1 0.3.0 --mode any
```

Strict Auto-to-Auto version comparison:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.3.0 0.3.1 --mode auto
```

## Validation report summary

A version comparison reports:

```text
tracks compared
STABLE / MINOR / SIGNIFICANT / CRITICAL counts
resolved genre match %
broad family match %
tempo equivalent %
key/mode match %
```

The JSON/CSV rows retain per-track drift metrics and reasons.

## Important limitation

History and convergence measure consistency, not objective genre correctness. A wrong model can be perfectly stable. Ground-truth/manual labels are still required to measure real classification accuracy.
