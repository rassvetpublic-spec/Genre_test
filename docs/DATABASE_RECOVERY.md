# Genre_test database recovery

Issue: #95

## Purpose

Genre_test keeps important state in SQLite databases. During development and portable testing, several valid databases can coexist: the current checkout history, legacy AppData history, portable histories, retrieval caches, and scoped retrieval snapshots.

`genre_test.db_recovery` provides a fail-closed way to find, compare, audit and copy-repair those databases without mutating the source.

## Safety model

The recovery tool follows these rules:

- discovery and audit open SQLite read-only;
- source fingerprint includes the main DB plus a non-empty WAL;
- volatile SHM and zero-length WAL files do not count as logical source changes;
- repair never works in place;
- repair uses SQLite Backup API into a temporary destination;
- `REINDEX` is applied to the destination by default;
- repaired output must pass `quick_check` and, by default, `integrity_check`;
- source fingerprint must match before and after the operation;
- output is published atomically;
- an existing output fails unless `--force` is explicit;
- with `--force`, the previous destination is preserved as a timestamped `.pre-repair-*.bak` file;
- corrupt page-level salvage is deliberately out of P0 scope. A source that fails integrity checks is rejected instead of being silently truncated.

The tool does not run MAEST, AST, BPM/key analysis, MERT or CLaMP.

## Database kinds

The audit classifies candidates by schema:

- `history` — contains `tracks` and `runs`;
- `scoped-history` — history schema plus `retrieval_history_scope_meta`;
- `retrieval` — contains `retrieval_meta`, `embedding_models` and `embeddings`;
- `unknown` — SQLite is readable, but its schema is not recognized as Genre_test state.

History reports include analyzer-version and analysis-mode counts when those columns exist.

## Discovery and ranking

Run from the repository checkout:

```powershell
cd C:\GIT\Genre_test
.\.venv\Scripts\python.exe -m genre_test.db_recovery scan --full-integrity
```

Default search roots include:

- the current checkout;
- the active `.genre_test` state directory;
- legacy Genre_test state location when present;
- the current working directory;
- immediate root/drive children that look like `Genre_test*` portable installations.

Additional roots can be supplied explicitly:

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery scan `
    "C:\Genre_test_0.4.0_portable" `
    "C:\GIT\Genre_test" `
    "D:\archive" `
    --full-integrity `
    --out-prefix ".genre_test\logs\db_recovery_scan"
```

Discovery accepts `history.sqlite3`, `retrieval.sqlite3`, and `.sqlite3` files inside recognizable Genre_test state/portable paths. SQLite `-wal` and `-shm` sidecars are never treated as standalone databases.

Ranking is deterministic. Healthy databases rank above unhealthy ones; recognized Genre_test schemas rank above unknown SQLite; within history/retrieval kinds, larger valid corpus/cache counts increase the score.

The score is a triage aid, not an automatic deletion or replacement decision.

## Audit one database

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery audit `
    "C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3" `
    --full-integrity
```

The JSON report contains:

- database kind;
- file size and mtime;
- WAL/SHM size;
- source fingerprint;
- journal mode;
- `quick_check` / optional `integrity_check`;
- important table counts;
- analyzer-version and analysis-mode distributions;
- scoped-history provenance metadata;
- deterministic ranking score;
- explicit error text when the database is unreadable/corrupt.

An unhealthy audit exits non-zero.

## Safe repair

Safe repair means building a new clean SQLite copy. It does not claim to recover page-level corruption.

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery repair `
    "C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3" `
    "C:\GIT\Genre_test\.genre_test\recovery\history_repaired.sqlite3" `
    --out-prefix ".genre_test\logs\history_repair"
```

Sequence:

```text
read-only source audit
    -> DB + non-empty WAL fingerprint
    -> SQLite Backup API to temp output
    -> REINDEX
    -> quick_check + integrity_check
    -> verify source fingerprint unchanged
    -> classify/audit temporary output
    -> atomic publish
    -> final output audit
```

If the requested output already exists, the command fails by default. `--force` is explicit and preserves the old destination as a timestamped backup before publishing the new copy.

Use `--no-reindex` only for diagnostic comparison. Use `--quick-only` only when a full integrity check is intentionally deferred.

## Corrupt databases

If a source fails `quick_check` / `integrity_check`, P0 returns a failure similar to:

```text
source failed safe-repair preflight; page-level salvage is not attempted
```

This is intentional. The next recovery tier, if needed, should be a separately reviewed salvage subsystem with row/table provenance and loss accounting. It must never be silently substituted for safe repair.

## Recovery after the v0.4 incident

The recovered v0.4 corpus demonstrated why database discovery must be first-class: the authoritative large history was in a portable installation rather than the current checkout state.

For that case, the expected workflow is:

```text
db_recovery scan
    -> audit candidate histories
    -> select recovered portable history
    -> history scope 0.4.0/auto
    -> retrieval catalog acceptance
    -> bounded CLaMP pilot
```

Database recovery does not replace retrieval history scoping; it provides the layer that finds and validates the correct source database before scoping/indexing begins.
