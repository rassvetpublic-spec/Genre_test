# Retrieval history scope snapshots

Issue: #92  
Parent acceptance: #39

## Why this exists

The recovered v0.4 portable history is a cumulative database, not a single-corpus database. It contains older 0.3.x / legacy analysis rows in addition to the completed v0.4 collection run. Passing that full database directly to retrieval therefore broadens the catalog beyond the intended #39 corpus.

The retrieval layer already accepts an explicit `--history` SQLite path. Instead of modifying or pruning the original history, Genre_test can now build a small **retrieval-only scoped snapshot** containing only one selected analyzer version / analysis mode.

The source history is always opened read-only. The builder fingerprints the source before and after the operation and writes the output through a temporary file plus atomic replace.

## Recovered v0.4 corpus

Source history used for the real acceptance run:

```text
C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3
```

Recovered collection root:

```text
D:\! Музыка
```

Target scope:

```text
analyzer_version = 0.4.0
analysis_mode     = auto
```

The recovered portable folder also contains exactly 10,436 v0.4 JSON result files. The cumulative history itself contains more tracks/runs because it includes earlier analysis versions; those unrelated rows must not silently become part of the #39 acceptance catalog.

## Build the scoped snapshot

From the current checkout:

```powershell
cd C:\GIT\Genre_test

$source = "C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3"
$scope  = "C:\GIT\Genre_test\.genre_test\catalog_scopes\v04_auto.sqlite3"

.\.venv\Scripts\python.exe -m genre_test.retrieval.history_scope `
    "$source" `
    "$scope" `
    --analyzer-version 0.4.0 `
    --analysis-mode auto
```

Default duplicate policy is `error`. That is intentional. If multiple matching runs exist for one `track_id`, stop and review the corpus instead of silently selecting one.

Only after review, a deterministic latest-run selection can be requested explicitly:

```powershell
--duplicate-policy latest
```

The tie-break is:

```text
analyzed_at DESC, rowid DESC
```

## Validate before CLaMP indexing

Do not start a full index immediately. First run status and acceptance against the scoped DB:

```powershell
.\.venv\Scripts\python.exe -m genre_test.retrieval.entrypoint `
    retrieval-index-status `
    --history "$scope"

.\.venv\Scripts\python.exe -m genre_test.retrieval.entrypoint `
    retrieval-catalog-audit `
    --history "$scope"
```

The reported `catalog_tracks` must match the scope builder's `selected_tracks` count.

For the recovered #39 corpus, the expected selection is the completed v0.4 Auto set, not the cumulative 10,677-track history view.

## Snapshot contents

The output SQLite contains:

- `tracks` — only selected content-addressed track IDs;
- `runs` — only the selected version/mode run for each track;
- `retrieval_history_scope_meta` — provenance and selection metadata;
- source indexes for the copied tables where available.

`tracks.last_path` is rewritten to the selected run's `source_path`, preventing a later unrelated history run from leaking its path into the scoped catalog.

The scoped file is **retrieval-only**. It is not a replacement for the original analysis history and must not be used as the authoritative archive for Validation or historical comparisons.

## Safety properties

- source history opened SQLite read-only;
- source DB/WAL fingerprint checked before and after build;
- source is never rewritten;
- output is built in a temporary sibling file;
- existing output is preserved unless `--force` is explicit;
- `PRAGMA integrity_check` must return `ok`;
- duplicate `track_id` values fail closed by default;
- no MAEST/AST/BPM/key re-analysis;
- no CLaMP model is started by the scope builder.

## Acceptance sequence for #39

```text
portable v0.4 history
    -> build scoped 0.4.0/auto snapshot
    -> retrieval-index-status --history <scope>
    -> retrieval-catalog-audit --history <scope>
    -> bounded full-track CLaMP pilot
    -> second unchanged pilot: cache-hit / zero recompute
    -> full track-level index
    -> acceptance >=99% readable or individually explained failures
    -> segment subset cost review
    -> only then consider segment --all
```

The original portable database and portable `results` directory should be retained until #39 acceptance and backup verification are complete.
