---
title: "Genre_test Roadmap"
doc_type: status
area: project
status: active
summary: "Release and architecture sequence from active v0.5 retrieval through the SUPERCOMBINE workstation and v1.0 integration."
tags:
  - область/project
  - тип/status
  - статус/active
---

# Genre_test Roadmap

## Product north star

Genre_test развивается в **local-first studio-finish workstation for generative songs**.

```text
Generated mix / stems
  -> Analyze / Catalog / Search
  -> Technical QC + timestamped markers
  -> Repair
  -> Stems / Vocal
  -> Mix / Master
  -> synchronized Compare
  -> Metadata / Delivery
  -> studio-ready export
```

Long-term epic: **#49 SUPERCOMBINE**.

Boundary rules:

- source audio immutable;
- measured/model evidence separated from description/recommendation;
- derived assets carry lineage/processing manifests;
- optional heavy backends fail independently;
- no detector-evasion, watermark stripping or provenance concealment objective.

## Current line — `0.5.0.dev0`

**0.5.0.dev0 — active development; no packaged stable release is currently published**

Active epic: **#26 CLaMP 3 semantic retrieval**.

Protected core analysis remains MAEST + AudioSet AST + BPM/key/native metadata -> deterministic `AudioProfile schema 4`. Retrieval is independent and optional.

Selected retrieval family:

```text
Audio -> MERT -> CLaMP 3 SAAS
Text  -> XLM-R -> CLaMP 3 SAAS
```

Runtime decision: **selected isolated persistent Python 3.12 CLaMP 3 sidecar runtime (#27 complete)**.

**#27 is complete:** the selected v0.5 architecture is an isolated persistent Python 3.12 subprocess sidecar. Python 3.13/3.12 remain the main application policy, while the pinned CLaMP 3 runtime keeps its isolated Python 3.12 compatibility boundary.

Current foundation already includes versioned schemas, isolated sidecar, persistent embeddings/index, audio/text search, segment/representative search, CLI/export/benchmark tooling and model-free `mfcc-acoustic78` benchmark baseline.

Remaining v0.5 gates are tracked by live Issues and `docs/CLAMP3_TODO.md`, including:

- real catalog coverage/cache acceptance (#30/#39);
- real audio similarity/relevance acceptance (#31);
- paired RU/EN text relevance acceptance (#32/#36);
- segment subset cost/relevance acceptance (#33);
- deterministic Core Sound (#43);
- TechnicalProfile expansion where validated (#45);
- optional zero-shot/tempo-map experiments (#37/#44);
- Windows/portable/release graduation (#38/#40/#41);
- Catalog/Search integration into the new Workstation (#34).

## Pre-refactor boundary — current

The old plan to add new Catalog/Search presentation directly to the historical Tk GUI is superseded as an implementation target.

Functional retrieval requirements remain; presentation ownership moves to the SUPERCOMBINE workstation.

```text
#184 pre-refactor docs/knowledge freeze
        |
        v
#171 durable exact-head QA contract
        |
================ REFACTOR BOUNDARY ================
        |
        v
#164 Workstation P1
```

Existing Tk GUI and CLI remain supported compatibility surfaces during migration. After this boundary, new product features do not expand Tk solely to satisfy roadmap items.

## Workstation migration sequence

Canonical sequence from `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`:

1. **P0 — DONE**: donor/provenance + architecture freeze (#160 / merged #161).
2. **P1 — #164**: workstation shell, RU/EN, local application-service/API/job facade, minimal runtime HUD adapter.
3. **P2 — #34**: existing Analyze/Catalog/Search capabilities wired into workstation; no duplicate retrieval backend.
4. **P3 — Compare transport kernel**: common aligned transport, loop/playhead, candidate switch, loudness-match seam and Delta seam compatible with #54.
5. **P4 — runtime HUD completion**: full presentation of canonical Resource Monitor/runtime state and future #55 seam.
6. **P5 — Repair UI**: #50 candidates through common P3 transport.
7. **P6 — Stems/Vocal UI**: #51/#52 through common P3 transport.
8. **P7 — Master UI**: Genre_test mastering backend, optional Ozone/REAPER, common P3 transport.
9. **P8 — Project/Vault/Delivery**: #53/#56 lineage, metadata and export integration.
10. **v1.0**: one resumable project/session over the full chain.

## Correctness gates before Workstation P2

Issue #94 is a hard gate: an explicit missing/invalid `--history` path must fail closed instead of appearing as a valid empty catalog.

The future local API must map source/infrastructure errors into structured failures, never `200 OK / tracks: 0` for a failed prerequisite.

## v0.6 — Repair & Stem Lab

Primary product issues:

- #50 generative artifact remediation/restoration;
- #51 vocal repair;
- #52 stem separation/repair/recombination;
- #63 Apollo restoration research where source eligibility/provenance permits.

Shared rules:

- Safe / Probe / Refine;
- immutable source + derived candidate identity;
- objective before/after QC plus loudness-matched listening;
- clean-control over-processing guard;
- `FULL_MIX_WINS`, `REGENERATE_SOURCE` and `INCONCLUSIVE` are valid outcomes;
- no repair wins from marker reduction alone.

## v0.7 — Studio Finish / mastering orchestration

Planned:

- versioned `MasteringBackend` request/result/manifest contract;
- REAPER render-host bridge for Ozone 12 Advanced;
- existing `mastering/ozone12` XML/config/tooling boundary;
- Safe / Probe / Refine mastering candidates;
- pre/post TechnicalProfile gates;
- backend-neutral drum-attack, mono-loss, stereo and decoded-codec checks;
- delivery normalization/compliance profiles.

### Comparison split

Full #54 remains the v0.7 synchronized A/B/X Comparison Lab: blind sessions, annotations, ratings, 2–12 candidates, persistence and reviewer evidence.

Only its **transport kernel** is pulled forward to Workstation P3 so Repair/Stems/Master never create private competing players.

## v0.8 — Metadata / Vault / Delivery

- #53 media tag auditor and reversible batch fix;
- #56 local asset vault with integrity, lineage, processing/model provenance and cleanup planning;
- final delivery package with checksums/reports/metadata where appropriate.

Identity metadata is never silently overwritten from model inference.

## v0.9 — Runtime orchestration / ComfyUI / Product MCP

- #46 thin Genre_test-owned ComfyUI bridge over stable local contracts;
- #55 shared `ModelRuntimeManager` / VRAM scheduler;
- stable local job API with progress/heartbeat/Safe Stop;
- **Track P Product MCP façade** over stable APIs.

### Track Q — cross-cutting QA infrastructure

Option C is already selected. Read-only Track Q engineering/QA evidence infrastructure may evolve outside release numbering without advancing product MCP scope.

#155 `ReviewEvidencePackV1` is currently `PARKED_READY` during the refactor boundary train. #171 durable QA verdict normalization is handled first.

## v1.0 — Integrated SUPERCOMBINE

Target persistent workflow:

```text
INGEST
 -> ANALYZE
 -> SEARCH / REFERENCE
 -> QC
 -> REPAIR
 -> STEMS / VOCAL (optional)
 -> MIX / MASTER
 -> A/B/X REVIEW
 -> TAG / DELIVERY
```

Graduation principles:

- resumable project/session;
- immutable source;
- explicit derived lineage;
- reproducible processing/model identities;
- heavy models optional and diagnosable;
- final objective QC + human review;
- Russian-first user documentation;
- real generative-song end-to-end fixtures;
- explicit third-party provenance/terms;
- no anti-detector-evasion objective.

## Knowledge and authoring layer

At the refactor boundary the repository adopts the Obsidian-aware Markdown authoring contract in `docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md`.

Historical unchanged Markdown is grandfathered by `MARKDOWN_LEGACY_BASELINE.json`; new or modified human-maintained Markdown must migrate to the controlled passport. This is a repository-authoring rule, not a separate product phase.

## Source of execution truth

This roadmap defines sequence and ownership. Exact execution state is always:

```text
Genre_test/main
+ live GitHub Issues/PRs
+ assigned Issue contract
```

Planning text never overrides a newer merged contract or live task state.
