---
title: "Retrieval Explicit History Source Contract"
doc_type: protocol
area: retrieval
status: canonical
summary: "Fail-closed validation and structured error mapping for explicitly selected retrieval analysis-history SQLite sources."
tags:
  - область/retrieval
  - тип/protocol
  - статус/canonical
---

# Retrieval Explicit History Source Contract

## Scope

This contract applies when a retrieval command explicitly receives `--history <path>` or `--history=<path>`.

It covers every retrieval command family that consumes analysis history, including status, index/rebuild, segment status/index, search, catalog audit, retry-missing and benchmark execution.

## Invariant

```text
explicit history source
-> validate read-only before Typer/backend dispatch
-> usable required schema OR stable source failure
```

An explicit history failure must never be converted into a successful empty catalog.

## Required schema and read path

The selected SQLite database must be an existing regular file and expose the minimum analysis-history columns retrieval reads:

```text
tracks.track_id
tracks.last_path
runs.track_id
runs.result_json
runs.analyzed_at
```

The current retrieval catalog selection also orders candidate `runs` records by `r.rowid`. Explicit-source validation therefore verifies that `runs.rowid` is queryable; a `WITHOUT ROWID` layout without an equivalent `rowid` column is not a compatible explicit history source for the current reader.

Validation opens SQLite with `mode=ro` and runs `PRAGMA quick_check`. It does not create, migrate, alter or otherwise mutate the explicit database.

## Structured failure envelope

`HistorySourceError.to_dict()` is the repository-local machine contract for future Workstation/API adapters:

```json
{
  "error": "history_source_error",
  "code": "history_source_missing | history_source_invalid_path | history_source_invalid_schema | history_source_corrupt | history_source_unreadable",
  "path": "<selected path>",
  "message": "<stable human-readable explanation>"
}
```

The code meanings are:

- `history_source_missing` — the explicitly selected regular file does not exist;
- `history_source_invalid_path` — explicit option syntax selected an empty path such as `--history=`;
- `history_source_invalid_schema` — required tables, columns, or the current `runs.rowid` read prerequisite are absent;
- `history_source_corrupt` — SQLite opens but `PRAGMA quick_check` reports corruption;
- `history_source_unreadable` — the file cannot be read as the required SQLite source.

Schema failures may additionally expose `missing_tables` and/or `missing_columns`.

The retrieval executable maps all `HistorySourceError` variants to the existing stable source-file exit code `23` and writes the structured envelope to stderr. Backend/model dispatch does not begin.

A future local HTTP/API adapter should preserve the same `error`, `code`, `path` and schema-detail fields when mapping the failure to an HTTP response. It must not translate this condition into `200 OK` with an empty catalog.

## Option parsing boundary

Pre-dispatch validation inspects `--history` only for commands that actually own that option. A standalone `--` ends option scanning, so later positional values retain normal Click/Typer meaning. A single-dash path value such as `--history -missing.sqlite3` is still an explicit path and is validated; callers may also use `./-missing.sqlite3` for clarity.

## Implicit default history

When no explicit `--history` is supplied, this pre-dispatch validator does nothing. Existing default history creation/migration ownership and first-run behavior remain unchanged.

This distinction is intentional:

```text
explicit path -> caller asserts a prerequisite exists -> fail closed
implicit default -> existing application lifecycle owns creation/migration
```

## Non-goals

- changing catalog identity, embeddings, ranking, filters or retrieval quality;
- changing the default history schema or migration path;
- creating missing explicit databases;
- repairing arbitrary SQLite corruption;
- starting CLaMP or other model backends during validation.
