---
title: "Genre_test Workstation P1 Contract"
doc_type: protocol
area: project
status: active
summary: "P1 contract for the localhost-only Genre_test workstation shell, RU/EN foundation, lightweight local API and canonical Resource Monitor adapter."
tags:
  - область/project
  - тип/protocol
  - статус/active
---

# Genre_test Workstation P1

Tracking: **#164**
Architecture owner: `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`
Donor provenance: `docs/SHIMMER_EXTERNAL_REFERENCE.md`

## Scope

P1 establishes one optional local workstation surface without replacing existing CLI/Tk entry points or changing analysis, retrieval, repair, mastering or audio semantics.

Implemented boundary:

- package namespace: `src/genre_test/workstation/`;
- explicit CLI entry point: `genre-test-workstation`;
- localhost-only stdlib HTTP server;
- packaged static workstation shell;
- full navigation skeleton: Project, Analyze, Catalog, Search, Repair, Stems, Master, Compare, Delivery, Settings;
- RU default / EN fallback translation catalog with parity validation;
- atomically persisted workstation language setting under Genre_test runtime state;
- versioned `/api/v1/*` shell contracts for health, navigation, capabilities, settings, jobs and runtime telemetry;
- contract-only P1 job/status/cancel seam; no domain backend execution is implied;
- minimal runtime HUD adapter over the existing `genre_test.resource_monitor` collector;
- source/output collision guard for future derived assets;
- structured JSON errors and bounded request bodies.

## Authority boundary

The workstation is an interface and application-service facade, not a new source of project truth.

```text
web shell
  -> workstation service/API
  -> existing Genre_test owners
```

P1 does not create a second analyzer, retrieval backend, resource poller, mastering engine, project database or audio-processing path.

The canonical Resource Monitor remains `src/genre_test/resource_monitor.py`. The workstation runtime adapter imports it only when runtime telemetry is requested.

## Heavy-import boundary

Importing or starting the P1 workstation shell must not eagerly import Torch, Transformers, librosa, retrieval or mastering backends. Optional/heavy domain services remain behind later phase adapters.

## Network boundary

The P1 server accepts only loopback bind targets. `0.0.0.0` and other non-loopback interfaces are rejected. The shell sets restrictive browser response headers and does not expose CORS or remote-listen configuration.

## Donor boundary

Pinned Shimmer reference: `henricksmedia/shimmer@ff8344ae1a77bd7eb5be46b55c83813e923d3d2c`.

P1 uses the donor only for bounded UI/workstation design reference. Server, i18n, API contracts, settings and runtime integration are Genre_test-owned reimplementations. Changelog-only donor code is not represented as copied source.

## Deferred surfaces

These navigation entries exist in P1 but remain explicitly deferred:

- Analyze / Catalog / Search -> P2;
- Compare common transport -> P3;
- complete Resource HUD -> P4;
- Repair -> P5;
- Stems -> P6;
- Master -> P7;
- Delivery/project-vault integration -> P8.

A deferred surface must not silently execute a private or duplicate backend.

## Validation

`tests/test_workstation_p1.py` verifies:

- packaged static shell assets;
- localhost-only binding;
- security headers;
- health/navigation/capability contracts;
- RU/EN catalog parity and persistence;
- structured error behavior;
- job heartbeat/progress/cancel seam;
- source immutability guard;
- Resource Monitor field adaptation and explicit unavailable state;
- clean workstation import without optional heavy backends.

`AUDIO_SCIENCE: NOT_APPLICABLE` — P1 changes interface/application-service plumbing only.
