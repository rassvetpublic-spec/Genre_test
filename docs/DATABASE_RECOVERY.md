---
title: "Genre_test Database Recovery"
doc_type: runbook
area: project
status: canonical
summary: "Канонический fail-closed workflow поиска, read-only аудита и атомарного repair SQLite с внешним access journal и provenance derived copies."
tags:
  - область/project
  - тип/runbook
  - статус/canonical
---

# Genre_test database recovery

Issues: #95, #97

## Purpose

Genre_test keeps important state in SQLite databases. During development and portable testing, several valid databases can coexist: the current checkout history, legacy AppData history, portable histories, retrieval caches, and scoped retrieval snapshots.

The canonical operator entry point is now `genre_test.db_recovery_provenance`. It preserves the fail-closed recovery core while adding the external database-access journal and embedded provenance for newly created derived databases. The lower-level `genre_test.db_recovery` module remains an implementation/core API and is not the documented operator CLI.

## Safety model

The recovery tool follows these rules:

- discovery and audit open SQLite read-only;
- source fingerprint includes the main DB plus a non-empty WAL;
- volatile SHM and zero-length WAL files do not count as logical source changes;
- read/audit provenance is written to the separate `.genre_test/database_access.sqlite3` journal, never into the audited source;
- the access journal is excluded from recovery discovery and cannot audit/repair itself;
- journal-write failure is explicit but does not turn a valid read-only audit into a source mutation;
- repair never works in place;
- repair uses SQLite Backup API into a temporary staging destination;
- `REINDEX` is applied to the staging destination by default;
- derived-database provenance is written and validated on staging before publication;
- repaired output must pass `quick_check` and, by default, `integrity_check` after provenance is present;
- source fingerprint must match before and after the operation;
- output is published atomically only after the provenance-enriched staging copy is valid;
- an existing output fails unless `--force` is explicit;
- with `--force`, the previous destination is displaced only after staging/provenance validation and is preserved as a timestamped `.pre-repair-*.bak` file;
- publication failure rolls the prior destination back when one existed;
- corrupt page-level salvage is deliberately out of P0 scope. A source that fails integrity checks is rejected instead of being silently truncated.

The tool does not run MAEST, AST, BPM/key analysis, MERT or CLaMP.

## Database kinds

The audit classifies candidates by schema:

- `history` — contains `tracks` and `runs`;
- `scoped-history` — history schema plus `retrieval_history_scope_meta`;
- `retrieval` — contains `retrieval_meta`, `embedding_models` and `embeddings`;
- `unknown` — SQLite is readable, but its schema is not recognized as Genre_test state.

History reports include analyzer-version and analysis-mode counts when those columns exist. Databases without embedded provenance remain valid and are reported as `unknown/legacy` rather than being mutated or rejected.

## Discovery and ranking

Run from the repository checkout:

```powershell
cd C:\GIT\Genre_test
.\.venv\Scripts\python.exe -m genre_test.db_recovery_provenance scan --full-integrity
```

Default search roots include:

- the current checkout;
- the active `.genre_test` state directory;
- legacy Genre_test state location when present;
- the current working directory;
- immediate root/drive children that look like `Genre_test*` portable installations.

Additional roots can be supplied explicitly:

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery_provenance scan `
    "C:\Genre_test_0.4.0_portable" `
    "C:\GIT\Genre_test" `
    "D:\archive" `
    --full-integrity `
    --out-prefix ".genre_test\logs\db_recovery_scan"
```

Discovery accepts `history.sqlite3`, `retrieval.sqlite3`, and `.sqlite3` files inside recognizable Genre_test state/portable paths, except the canonical access journal itself. SQLite `-wal` and `-shm` sidecars are never treated as standalone databases.

Ranking is deterministic. Healthy databases rank above unhealthy ones; recognized Genre_test schemas rank above unknown SQLite; within history/retrieval kinds, larger valid corpus/cache counts increase the score.

The score is a triage aid, not an automatic deletion or replacement decision.

## Audit one database

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery_provenance audit `
    "C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3" `
    --full-integrity
```

The JSON report contains:

- database kind;
- file size and mtime;
- WAL/SHM size;
- source fingerprint before/after and `target_unchanged` evidence;
- journal mode;
- `quick_check` / optional `integrity_check`;
- important table counts;
- analyzer-version and analysis-mode distributions;
- scoped-history provenance metadata;
- embedded database provenance when present;
- external last-read/write/repair/scope-build/integrity/build evidence when known;
- explicit journal-write status;
- deterministic ranking score;
- explicit error text when the database is unreadable/corrupt.

An unhealthy audit exits non-zero. A healthy source audit can still report a journal failure separately; that failure never authorizes source mutation.

## Safe repair

Safe repair means building a new clean SQLite copy. It does not claim to recover page-level corruption.

```powershell
.\.venv\Scripts\python.exe -m genre_test.db_recovery_provenance repair `
    "C:\Genre_test_0.4.0_portable\.genre_test\history.sqlite3" `
    "C:\GIT\Genre_test\.genre_test\recovery\history_repaired.sqlite3" `
    --out-prefix ".genre_test\logs\history_repair"
```

Sequence:

```text
read-only source audit
    -> DB + non-empty WAL fingerprint
    -> SQLite Backup API to provenance staging output
    -> REINDEX
    -> base quick_check + integrity_check
    -> write embedded derived-database provenance on staging
    -> quick_check + integrity_check with provenance present
    -> verify source fingerprint unchanged
    -> only now backup existing destination when --force
    -> atomic staging -> requested output publish
    -> final output audit
    -> external source/output access events
```

If staging provenance insertion or validation fails, the requested output is not published and an existing `--force` destination is not displaced. If publication/final audit fails after an existing destination was backed up, the prior destination is restored.

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
db_recovery_provenance scan
    -> audit candidate histories
    -> select recovered portable history
    -> history scope 0.4.0/auto
    -> retrieval catalog acceptance
    -> bounded CLaMP pilot
```

Database recovery does not replace retrieval history scoping; it provides the layer that finds and validates the correct source database before scoping/indexing begins. Scoped-history construction records source/read and derived/write `scope-build` provenance through the same external journal contract.

## Authority and compatibility

`src/genre_test/db_recovery.py` remains the stable recovery core used internally by the provenance adapter. Operator documentation must use `genre_test.db_recovery_provenance` (or the installed provenance-aware console script) so recovery cannot silently bypass the external journal and derived provenance contract.

Legacy databases remain readable without embedded metadata. Provenance is never backfilled into a source merely because it was scanned or audited.
