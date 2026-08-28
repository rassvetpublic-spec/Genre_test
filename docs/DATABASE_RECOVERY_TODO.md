# Database Recovery TODO

This checklist tracks follow-up work after the v0.4 corpus recovery and the safe database-recovery subsystem.

## Completed foundation

- [x] Explicit retrieval history scoping for the recovered `0.4.0 / auto` corpus (#92 / PR #93).
- [x] Real acceptance: 10,436 scoped tracks/runs, 10,360 readable paths, 76 missing, >=99% readable.
- [x] Database discovery, read-only audit, deterministic ranking, JSON/Markdown reports and copy-on-write repair (#95 / PR #96).
- [x] DB + non-empty WAL fingerprinting; volatile SHM and zero-length WAL are not treated as logical mutations.
- [x] Windows Unicode-safe retrieval console output.

## P0 follow-up

- [ ] **#94 — fail closed on an explicit missing/invalid `--history` path.** Retrieval commands must never turn a missing requested history into a successful zero-track catalog.
- [ ] **#97 — database access provenance and runner/build identity.** Keep an external `.genre_test/database_access.sqlite3` journal so read-only audits do not mutate target databases. Track last read/write/repair/scope-build/integrity-check plus app version, commit/build fingerprint, host/process and result.
- [ ] Expose legacy provenance as `unknown/legacy` rather than rejecting older v0.3/v0.4 databases that lack new metadata.
- [ ] Add deterministic DB/build identity metadata to newly created Genre_test databases and derived snapshots without retroactively rewriting historical source DBs.

## P1 recovery

- [ ] **#98 — separate salvage tier for damaged SQLite.** Only for databases that fail safe-repair preflight; source remains immutable, output is always separate, recovered/lost tables and rows must be reported explicitly.
- [ ] Evaluate official SQLite recovery/export mechanisms before any custom page-level parsing.
- [ ] Add damaged-database fixtures and loss-accounting regression tests.

## Operational rules

- Recovery scan/audit is read-only with respect to the target database.
- Safe repair is copy-on-write only and never automatically replaces the active DB.
- Salvage is never silently substituted for safe repair.
- Filesystem `LastAccessTime` is non-authoritative evidence only.
- Do not delete historical candidate databases automatically based on ranking.
- Keep source fingerprints and provenance links for all derived scope/repair/salvage outputs.
- No MAEST/AST/MERT/CLaMP processing is part of database recovery itself.
