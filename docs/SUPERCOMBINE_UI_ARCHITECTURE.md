# Genre_test SUPERCOMBINE workstation UI architecture

Status: **P0 architecture / owner-approved direction**
Tracking Issue: **#160**
Parent epic: **#49**
Approved: **2026-08-30**

## 1. Product decision

`Genre_test` is the product. The future SUPERCOMBINE is one local-first workstation, not a collection of separately authoritative applications.

Shimmer is an **authorized donor and UI prototype**. Direct code migration is allowed from recoverable/pinned donor source; changelog-only local additions remain requirements until their exact source is supplied and pinned. Existing Genre_test domain contracts remain authoritative.

The historical `OZONE12_MASTERING_LAB` is not revived. Its Universal Core v1.4.1 is already migrated and preserved as provenance; Ozone 12 remains an optional mastering backend under the existing Genre_test mastering boundary.

## 2. Target user workflow

```text
PROJECT / SOURCE
   |
   +-> ANALYZE
   |     AudioProfile + Technical QC + markers
   |
   +-> CATALOG / SEARCH
   |     CLaMP retrieval + filters + references
   |
   +-> REPAIR
   |     full-mix repair candidates + Delta
   |
   +-> STEMS / VOCAL
   |     separation + per-stem repair + recombination
   |
   +-> MASTER
   |     mastering backend selection
   |     Ozone12/REAPER optional
   |
   +-> COMPARE
   |     synchronized A/B/X + loudness match + notes
   |
   +-> DELIVERY
         metadata + lineage + checksums + export
```

The source is immutable throughout the workflow.

## 3. Layer ownership

```text
+-----------------------------------------------------------+
| Genre_test workstation web UI                            |
| navigation / transport / visualizers / editors / A-B-X   |
+----------------------------+------------------------------+
                             |
                             v
+-----------------------------------------------------------+
| Local workstation API / job facade                       |
| requests / progress / cancel / project session / events  |
+----------------------------+------------------------------+
                             |
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
+---------------+   +----------------+   +------------------+
| Core services |   | Backend        |   | Shared technical |
| analysis      |   | adapters       |   | / QC services    |
| catalog       |   | repair/stems   |   | metrics/markers  |
| retrieval     |   | mastering      |   | provenance       |
+---------------+   +----------------+   +------------------+
        |                    |                    |
        +--------------------+--------------------+
                             |
                             v
+-----------------------------------------------------------+
| SQLite / project state / derived-asset manifests         |
+-----------------------------------------------------------+
```

### Genre_test owns

- analysis, AudioProfile and model evidence;
- TechnicalProfile/shared QC metrics;
- CLaMP/catalog/retrieval contracts;
- processing and derived-asset identity;
- project/session persistence;
- resource/runtime health;
- backend selection and failure semantics;
- A/B/X session truth and winner persistence;
- mastering request/result contracts;
- safety and provenance rules.

### Donor UI may contribute

From a pinned/recoverable donor revision:

- visual shell and dense studio layout patterns;
- responsive web controls;
- Single/Batch interaction patterns;
- waveform/spectrum/spectrogram visualizers;
- transport and loop UX;
- quick A/B switching;
- preset-browser ergonomics where preset semantics are Genre_test-owned;
- stem mixer/solo monitoring UX;
- project/recent/settings ergonomics;
- help/tooltip structure.

The owner changelog additionally defines RU/EN, Blackwell/Demucs, resource-HUD and fast-preview requirements. Changelog-only implementation details are not treated as directly portable code until their source is supplied and pinned.

## 4. Donor inventory policy

Every donor component must be classified before production import:

- `PORT` — recoverable code may be brought over with bounded namespace/style changes;
- `ADAPT` — recoverable implementation is useful but must be rewired to Genre_test contracts;
- `REIMPLEMENT` — retain UX/behavioral requirement but replace donor backend or unavailable implementation;
- `REJECT` — outside product boundary or duplicates canonical functionality;
- `EXPERIMENT` — audio/DSP idea requiring project fixtures and Audio Science before promotion.

Initial classification:

| Donor area | Classification | Genre_test treatment |
|---|---|---|
| pinned public `static/css/**` | PORT/ADAPT | starting visual grammar; Genre_test identity |
| pinned public `static/index.html` | ADAPT | split into workstation views/navigation |
| pinned public visualizer modules | ADAPT | wire to Genre_test assets/markers/compare sessions |
| pinned public Single/Batch controls | REIMPLEMENT/ADAPT | preserve UX, call Genre_test services |
| public preset-browser/controls | ADAPT | UX only; Genre_test owns semantics |
| changelog-only `i18n.js` | REIMPLEMENT until source is pinned | implement equivalent RU/EN contract in Genre_test |
| project/recent/settings UI | ADAPT | map to Genre_test project/session state |
| `shimmer/server.py` | REIMPLEMENT | one Genre_test local API; no second server truth |
| job/preview code | ADAPT/REIMPLEMENT | common progress/cancel and #54 compare contracts |
| stems code | ADAPT/EXPERIMENT | only if exact source is pinned and #52 gates pass |
| mastering code | REIMPLEMENT | Genre_test `MasteringBackend` is authoritative |
| donor resource polling backend | REJECT DUPLICATE | use existing Genre_test Resource Monitor |
| DSP heuristics | EXPERIMENT | fixtures + damage guards required |
| detector-evasion objective | REJECT | never a production objective or optimization metric |

`PORT` does not mean default behavior is trusted.

## 5. Navigation model

```text
Project | Analyze | Catalog | Search | Repair | Stems | Master | Compare | Delivery | Settings
```

### Project
- source/derived asset tree;
- recent projects;
- processing lineage;
- current stage and pending jobs.

### Analyze
- current analysis output;
- Technical QC and timestamped markers;
- explicit evidence origin labels.

### Catalog / Search
- existing catalog/retrieval services;
- text/audio queries;
- representative/custom segment search;
- no duplicate embedding implementation in UI backend.

### Repair
- BYPASS + Safe / Probe / Refine candidates;
- Removed/Delta audition through the common compare transport;
- loudness-matched preview;
- damage warnings.

### Stems
- optional separation backend;
- vocals/drums/bass/other monitoring;
- per-stem repair handoff;
- recombination integrity and phase/latency checks.

### Master
- backend-neutral mastering request;
- Ozone12/REAPER optional backend;
- existing Ozone XML/config rules remain canonical;
- preflight, candidates and codec/mono/transient checks.

### Compare
- #54 common A/B/X session and transport;
- sample/time alignment;
- loudness match;
- blind mode;
- notes and selected winner.

### Delivery
- metadata audit;
- final technical gate;
- delivery formats where applicable;
- manifests/checksums/reports.

## 6. Workstation API principles

The web shell must not import heavy model/DSP modules directly.

Required properties:

- localhost-only by default;
- versioned request/result payloads where domain contracts exist;
- asynchronous job identity for long operations;
- progress + heartbeat + structured error;
- Safe Stop/cancel;
- explicit backend health and optional-unavailable states;
- no hidden model downloads;
- source path never used as an output target;
- one derived-asset registration path;
- stable event model suitable for later automation/MCP façade.

Transport technology is an implementation detail.

## 7. Resource/runtime integration

The Shimmer HUD concept is useful presentation design, but backend truth comes from existing Genre_test resource/runtime services.

P1 may expose a minimal adapter needed for the workstation shell. P4 expands this into the complete resource surface and future #55 lifecycle events.

Do not create competing GPU/CPU/RAM polling semantics. Unsupported telemetry is explicit `N/A`.

## 8. Preview and listening contract

**The common #54-compatible transport is a prerequisite for Repair/Stems/Master comparison surfaces, not a late add-on.**

Build the common transport in P3 before P5/P6/P7 candidate surfaces depend on it:

```text
source/candidate assets
 -> alignment
 -> optional loudness match
 -> common loop/playhead
 -> instant switch
 -> optional Delta
 -> reviewer notes/ratings
```

No private repair-only transport should be created. No candidate may win only because it is louder.

## 9. Repair safety boundary

The owner changelog contains experiments aimed at reducing AI-detector risk. That objective is outside Genre_test.

Do not port:

- detector-score optimization loops;
- “AI risk before/after” as a repair success metric;
- watermark/provenance stripping;
- origin-concealment behavior;
- detector-specific evasion presets.

A generic DSP primitive may be reconsidered only when independently specified for an **audible defect** and validated under #50/#51/#52 against BYPASS, clean controls, loudness-matched listening, Delta contamination, transient retention, stereo/mono preservation, codec robustness and musical damage.

## 10. Ozone integration

The supplied `OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1` archive has SHA-256:

`9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7`

This matches the already migrated Genre_test provenance snapshot. Therefore:

- do not add another Universal Core copy;
- do not re-create the standalone Ozone runtime;
- reuse `src/genre_test/mastering/ozone12/` and related docs/config/tools namespaces;
- build the future REAPER/Ozone execution bridge natively in Genre_test;
- expose it only through the mastering backend contract.

## 11. Compatibility and rollout

Until the workstation reaches its graduation gate:

- current desktop GUI remains usable;
- current CLI remains usable;
- v0.5 retrieval remains independently usable;
- optional workstation/API failure does not break ordinary analysis startup;
- existing SQLite history is not silently migrated destructively.

## 12. Implementation order

This order is authoritative for the donor-workstation migration and is aligned with `SUPERCOMBINE_SHIMMER_DONOR_TODO.md`:

1. **P0 — donor/provenance and architecture freeze** (#160).
2. **P1 — workstation shell + RU/EN foundation + local API + minimal runtime-HUD adapter** (#164).
3. **P2 — existing Analyze/Catalog/Search services in workstation**.
4. **P3 — common #54-compatible transport, preview, A/B/X and Delta foundation**.
5. **P4 — complete resource HUD/runtime integration and #55 seam**.
6. **P5 — Repair UI wired to #50 and the P3 common transport**.
7. **P6 — Stems/Vocal UI wired to #51/#52 and the P3 common transport**.
8. **P7 — mastering UI wired to Genre_test Ozone/REAPER backend and the P3 common transport**.
9. **P8 — project/vault/delivery integration**.
10. **v1.0 — one resumable project/session across the full chain**.

Each production slice requires its own Issue/claim/PR and exact-head gates.

## 13. First graduation gate

P0 is complete when:

- donor identity, owner authorization and direct-code rights are recorded;
- direct code donor scope is limited to recoverable/pinned source;
- changelog-only additions are explicitly requirements rather than recoverable code;
- donor module inventory is explicit;
- Ozone duplicate import is prohibited;
- detector-evasion branch is excluded;
- common transport dependency order is unambiguous;
- existing Genre_test product boundaries remain intact;
- no production code is changed by the P0 PR.