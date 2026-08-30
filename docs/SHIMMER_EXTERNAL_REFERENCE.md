# Shimmer donor and migration source for Genre_test

Status: **AUTHORIZED DONOR / UI PROTOTYPE / EXPERIMENT SOURCE**
Tracking: **#160**
Snapshot date: **2026-08-30**
Canonical UI architecture: `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`

> Filename is retained for stable links. The previous `external-only / do-not-copy` classification is superseded by the owner authorization recorded on 2026-08-30.

## Decision

The project owner explicitly authorized reuse and rework of Shimmer for `Genre_test` and defined the supplied Shimmer work as:

1. a source of SUPERCOMBINE to-do items;
2. a prototype for the future integrated workstation interface.

Shimmer may therefore contribute **code, UI structure and workflow implementations**, subject to adaptation to Genre_test contracts and review gates.

It is not imported as a second product or a second source of runtime truth.

Recommended role:

```text
AUTHORIZED_DONOR
+ UI_PROTOTYPE
+ EXPERIMENT_SOURCE
```

Not:

```text
NESTED_PRODUCT
SECOND_RUNTIME_TRUTH
UNVALIDATED_PRODUCTION_DEFAULTS
```

## Donor identity and recoverability

Public repository:

`https://github.com/henricksmedia/shimmer`

Pinned public baseline used for direct code migration:

`ff8344ae1a77bd7eb5be46b55c83813e923d3d2c`

The public baseline contains a Python backend under `shimmer/` and a web workstation-style UI under `static/`, including Single/Batch workflows, processing-chain controls, visualizers, presets, project/recent state, stems and mastering-related surfaces.

The owner-supplied 2026-08-30 changelog describes additional local work beyond that public baseline, including RU/EN i18n, Blackwell/Demucs work, resource-monitor UI concepts, live loop/A-B preview and stem workflows.

**Important provenance boundary:** the changelog is requirements/backlog evidence, not a recoverable code revision. Until an exact local source archive or commit is supplied and hash-pinned, code that exists only in that changelog must not be represented as directly portable donor code. Those features may be reimplemented from the documented requirements or replaced by equivalent Genre_test-owned implementations.

Therefore:

```text
pinned public commit -> eligible code donor
owner changelog only -> requirements / UX target / TODO
future supplied local source -> donor only after exact hash/revision is recorded
```

## Authorization and redistribution rights

The public donor repository currently advertises AGPL-3.0. The project owner has explicitly stated in the project conversation that Shimmer is their project, that licensing is not a blocker, and that its repository may be taken and reworked for the new Genre_test project.

For this owner-controlled migration, that statement is recorded as authorization to copy, modify, integrate and redistribute selected Shimmer source as part of Genre_test, including adaptation into the Genre_test repository and release line. The migration must still preserve source/provenance attribution so copied or substantially adapted components remain auditable.

If a later public release needs a formal copyright/license notice beyond this repository decision record, release packaging may add it without reopening the engineering permission to migrate the owner-controlled donor code.

This authorization applies only to code/assets for which the owner holds the required rights; third-party dependencies embedded in or used by Shimmer retain their own terms and must pass the normal Genre_test provenance gate.

## Architecture boundary

Existing `Genre_test` contracts take precedence over donor implementation choices.

```text
Shimmer donor UI / implementation ideas
              |
              v
Genre_test workstation UI
              |
              v
Genre_test local API / job facade
              |
      +-------+-------+
      |               |
      v               v
Genre_test core   backend adapters
analysis/QC/      repair/stems/
retrieval         mastering
```

Do not keep a parallel Shimmer production server, database truth, analyzer truth, resource monitor or mastering truth after migration.

## High-value donor areas

### 1. Workstation web UI

Direct donor candidates from the pinned public revision include:

- `static/index.html`;
- `static/css/**`;
- public `static/js/**` workstation modules such as visualizer, Single/Batch, controls, presets, recents and settings where present at the pinned revision.

The product identity becomes `Genre_test`; migrated calls terminate in Genre_test services/contracts.

### 2. RU/EN i18n

The owner changelog describes a broad `static/js/i18n.js` implementation, but that local implementation is not part of the pinned public revision. Treat it as a UX requirement until its exact source is supplied. P1 may implement an equivalent Genre_test-owned RU/EN layer without waiting for that source.

### 3. Cleanup before mastering

Keep the workflow principle:

```text
artifact analysis
 -> BYPASS | repair candidate
 -> repair QC
 -> mastering
 -> final codec / delivery audit
```

Repair and mastering remain separate decisions. A mastering stage must not hide an unresolved repair failure.

### 4. Removed / Delta audition

```text
original.wav
processed.wav
removed_delta.wav
```

Wanted musical content in Delta is a damage signal, not a success signal.

### 5. Loudness-matched A/B and live loop preview

The donor interaction patterns and owner changelog are UX inputs for #54. Genre_test converges them into one common comparison contract: synchronized playhead/loop, optional loudness matching, instant switching, representative loops, blind mode, notes/ratings and a persistent winner.

Timing claims from the changelog are not production guarantees until measured in Genre_test.

### 6. Stem workflow UX

Useful concepts include vocals/drums/bass/other cards, stem solo/monitoring, per-stem source/processed switching and recombination. Backend implementation must pass #52 runtime, provenance, phase/latency and recombination-integrity gates.

### 7. Resource HUD presentation

Reuse presentation ideas only. Genre_test already owns Resource Monitor/runtime truth; do not duplicate the polling backend.

### 8. High-band / M-S / transient-protection repair ideas

Useful hypotheses remain high-band-only repair, protected Mid/stronger Side processing, transient safety gates, artifact-family taxonomy and Delta inspection. No donor preset constant becomes a Genre_test default merely because it exists in donor code or changelog.

Required promotion evidence includes BYPASS, clean controls, loudness-matched listening, Delta contamination, transient retention, stereo/mono preservation, codec robustness where relevant, repeatability and failure behavior.

## Donor classification

The detailed inventory lives in `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`.

- pinned public UI/CSS/visualizer code: `PORT` or `ADAPT`;
- public Single/Batch/project/job UX: `ADAPT` / `REIMPLEMENT` against Genre_test services;
- changelog-only local implementations: `REIMPLEMENT` unless their exact source is later supplied and pinned;
- stems/preview implementations: `ADAPT` behind experimental gates when source is pinned;
- mastering implementation: `REIMPLEMENT` behind Genre_test `MasteringBackend` contracts;
- resource-monitor backend: `REJECT DUPLICATE`;
- unvalidated DSP/preset heuristics: `EXPERIMENT`;
- detector-evasion objectives: `REJECT`.

## Explicit detector-evasion exclusion

The supplied 2026-08-30 local changelog contains an `Anti-AI Vocoder Stealth Engine` whose stated goal includes lowering AI-detector scores and bypassing detector classifications.

That objective is outside Genre_test and must **not** be migrated into production scope.

Do not port or optimize detector-risk minimization, detector-specific success metrics, watermark/provenance stripping, origin concealment, or claims that processed audio is “human” because a detector score fell.

Generic DSP primitives found in those experiments may only be reconsidered as independently specified **audible defect** repair candidates under #50/#51/#52. Their success criterion is audible defect reduction with controlled musical damage, not detector evasion.

## Ozone relationship

Shimmer mastering code is not a replacement for the migrated Ozone knowledge/runtime boundary.

The owner-supplied `OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1` archive hashes to:

`9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7`

That is the same canonical snapshot already preserved in Genre_test. No second import is needed.

Active Ozone work stays under:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

The future workstation exposes Ozone only through the Genre_test mastering backend/orchestration layer.

## Migration protocol

For each donor component:

```text
1. Pin recoverable donor/source identity.
2. Confirm owner/third-party provenance for that component.
3. Classify PORT / ADAPT / REIMPLEMENT / REJECT.
4. Map donor concepts to Genre_test contracts.
5. Port only the minimum bounded component.
6. Add focused tests.
7. Preserve existing desktop GUI/CLI behavior during rollout.
8. Run QA; run Audio Science when audio/DSP semantics change.
9. Promote only after exact-head CI/review gates.
```

## Current priority

1. Freeze workstation architecture and donor provenance (#160).
2. Build Genre_test-owned web shell + RU/EN language layer.
3. Wire existing Analyze/Catalog/Search services.
4. Integrate canonical Resource Monitor.
5. Build common preview/A-B-X transport aligned with #54.
6. Add repair/stem surfaces behind #50/#51/#52.
7. Add mastering through Genre_test `MasteringBackend` and existing Ozone boundary.
8. Finish project/vault/delivery surfaces toward v1.0.

## Engineering conclusion

Shimmer is a **code donor and product-interface prototype**, not a parallel application. Direct code migration is limited to recoverable, pinned source; changelog-only local work remains a requirements source until its code is supplied. Genre_test keeps one runtime/domain truth and validates audio behavior independently.