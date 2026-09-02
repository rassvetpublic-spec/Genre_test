---
title: "Database Access Provenance"
doc_type: protocol
area: runtime
status: canonical
summary: "External provenance contract for Genre_test SQLite reads, repairs, scoped builds, and derived database identity without mutating audited source databases."
tags:
  - область/runtime
  - тип/protocol
  - статус/canonical
---

# Database Access Provenance

## Purpose

Genre_test must be able to answer **what accessed a SQLite database, when, in which mode, and with which build**, without changing an audited database merely because it was inspected.

Canonical ownership is split deliberately:

```text
audited SQLite database = source truth
external access journal = access-event truth
embedded provenance table = identity of newly created/derived database
recovery report = read-only view over those owners
```

`ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS` applies here directly. Access metadata is not written into an old source DB during scan/audit.

## External journal

Default location:

```text
.genre_test/database_access.sqlite3
```

The journal is keyed by the content fingerprint of the target DB whenever that fingerprint is available. If a target cannot be fingerprinted, a path-derived fallback key may be used only for recording the failed access attempt; it is not presented as a content identity.

Each access event records:

- target DB fingerprint and resolved path;
- UTC event timestamp;
- operation: `scan`, `audit`, `read`, `write`, `scope-build`, `repair`, `salvage`, or `integrity-check`;
- access mode: `readonly` / `readwrite`;
- Genre_test app version;
- Git commit when available;
- deterministic build fingerprint;
- build channel (`dev`, `portable`, `release`);
- process ID;
- host/computer identity;
- local OS user identity;
- Python implementation/version;
- success/failure and compact details.

Arbitrary environment variables, tokens, credentials, request payloads, and secrets are not journaled.

## Build fingerprint

The deterministic build fingerprint is derived only from stable build identity fields:

```text
schema marker
+ app version
+ Git commit or explicit unknown marker
+ build channel
```

Host name, OS user, PID, and Python runtime are event context and do **not** participate in the deterministic build fingerprint.

## Read-only invariant

Recovery/audit opens the target with SQLite URI `mode=ro` and compares the target fingerprint before and after the audit when the target can be fingerprinted.

Required invariant:

```text
read-only audit
-> source fingerprint before
-> audit/read
-> source fingerprint after
-> equal
```

The external journal is the only durable write caused by a successful read-only audit.

A journal failure must be explicit in the returned/report payload, but it must not corrupt or convert an otherwise valid read-only audit into a target-DB write. The target remains authoritative.

## Derived database provenance

Newly created or derived databases may contain:

```text
genre_test_database_provenance
```

Required identity fields include:

- database UUID;
- provenance schema version;
- DB/schema version when known;
- app version;
- build commit SHA when known;
- deterministic build fingerprint;
- build channel;
- `created_at` UTC;
- source fingerprint for derived DBs.

The table is written only to the new/derived output, never retrofitted into an audited legacy source as a side effect of reading it.

Old v0.3/v0.4 databases without the table remain readable and are reported as:

```text
status: unknown/legacy
```

Absence of provenance is not database corruption.

## Recovery adapter

The public `genre-test-db-recovery` command is routed through `genre_test.db_recovery_provenance`.

The stable `genre_test.db_recovery` module remains the recovery core. The provenance adapter adds:

- before/after fingerprint evidence;
- embedded provenance discovery;
- external journal writes;
- last-access summaries;
- provenance-aware JSON/Markdown views;
- metadata on newly repaired copies.

This keeps recovery mechanics separate from provenance/view concerns and limits regression surface.

## Derived report fields

Where evidence exists, recovery views expose:

- last read;
- last write;
- last repair;
- last scope-build;
- last integrity check;
- last accessing build;
- last accessing runner.

Unknown values remain explicit rather than inferred from filesystem `LastAccessTime`.

## Scope-build integration

A retrieval history scope build is a derived-database operation. Its source is read-only; its output is read-write and should carry both embedded derived provenance and external `scope-build` events. The source fingerprint remains the provenance link between source and derived snapshot.

## Failure policy

- Never mutate the audited source merely to record access.
- Never treat filesystem access time as authoritative provenance.
- Never hide a journal write failure; report it explicitly.
- Never let journal corruption silently rewrite source truth.
- Never invent build identity when Git metadata is unavailable; use an explicit unknown marker inside the deterministic fingerprint contract.
- Never make old databases unreadable because provenance metadata is absent.

## Obsidian use

This document is a human-maintained canonical protocol note and uses the repository Obsidian Markdown passport. Generated recovery reports are views and are not canonical owners of access or database identity facts.
