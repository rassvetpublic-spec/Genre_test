---
title: "Donor Intake Policy"
doc_type: protocol
area: project
status: canonical
summary: "Canonical admission gate for external donor components, separating product fit, provenance and bounded technical reuse from excluded product workflows."
tags:
  - область/project
  - тип/protocol
  - статус/canonical
---

# Donor Intake Policy

## Purpose

External projects may provide useful implementation patterns without becoming Genre_test products, runtimes or sources of truth. Every donor intake must classify both **what is useful** and **whether that thing belongs in the Genre_test product** before code migration starts.

Canonical invariant:

```text
DONOR KNOWLEDGE != PRODUCT SCOPE
```

A donor repository can be valuable even when most of its product surface is excluded.

## Required donor record

Every material donor intake must record:

```text
source_repository: <URL>
source_revision: <immutable commit/tag>
source_path: <path or bounded subsystem>
classification: PORT | ADAPT | REIMPLEMENT | REFERENCE
product_fit: IN_SCOPE | DONOR_ONLY | OUT_OF_SCOPE
target_owner: <Genre_test canonical service/contract/doc>
rights_note: <code/model/data terms or explicit review requirement>
```

### `classification`

- `PORT` — exact pinned source is eligible for direct migration and provenance is retained;
- `ADAPT` — pinned implementation is materially transformed behind Genre_test-owned contracts;
- `REIMPLEMENT` — behavior/requirement is reproduced without importing unrecoverable or unsuitable source;
- `REFERENCE` — architecture/operations evidence only; no source migration.

### `product_fit`

- `IN_SCOPE` — capability directly belongs in the approved Genre_test product boundary;
- `DONOR_ONLY` — a bounded technical primitive is useful for implementing an in-scope capability, but the donor product/workflow itself is not admitted;
- `OUT_OF_SCOPE` — capability/workflow is rejected from Genre_test product implementation.

`DONOR_ONLY` must never be used to smuggle an excluded workflow into navigation, release milestones or product ownership. It applies only to the explicitly bounded primitive being reused.

## Current Genre_test product boundary

### `IN_SCOPE`

- music/audio analysis and Technical QC;
- Catalog/Search/retrieval and similarity workflows;
- controlled repair/restoration and stem workflows;
- mastering/Ozone/REAPER integration owned inside Genre_test;
- comparison/listening/evidence workflows;
- detector robustness/evidence research that preserves known ground truth and reproducibility;
- project asset lineage, delivery and workstation/runtime infrastructure needed by those workflows.

### `DONOR_ONLY`

Examples are technical primitives whose donor-facing product is not adopted:

- process-tree containment and timeout cleanup;
- explicit requested/actual provider evidence and no-silent-fallback routing;
- doctor/deep-doctor diagnostics;
- sidecar heartbeat/liveness patterns;
- bounded UI/interaction patterns with pinned provenance;
- maintained separation implementations used as candidates/baselines under Genre_test contracts.

### `OUT_OF_SCOPE`

- dubbing product/workflow;
- audiobook production product/workflow;
- general-purpose TTS product;
- general-purpose voice-cloning product;
- film/video localization workflow.

`OUT_OF_SCOPE` components are rejected from product implementation. Reclassification requires a separate product-boundary decision, not a donor PR.

## Authority rule

```text
donor source / research source
  -> bounded evidence + provenance
  -> Genre_test-owned adapter/reimplementation
  -> canonical Genre_test service/contract
```

Never:

```text
donor server/database/model cache
  -> parallel production truth
```

Existing Genre_test owners override donor implementation choices.

## Detector research boundary

Detector robustness research under #80/#198 is in scope when experiments preserve known ground truth, exact processing history, detector identity/version and reproducible evidence.

A detector score is not mastering-quality truth. Ordinary repair/mastering must not silently optimize for detector-score reduction. Watermark/provenance stripping, hidden origin concealment and detector-specific production evasion remain rejected objectives.

## VoiceStudio boundary

Issue #199 may admit only bounded runtime/operations primitives from VoiceStudio as `DONOR_ONLY`, such as process containment, capability truth, doctor/deep-doctor patterns and heartbeat/liveness.

VoiceStudio dubbing, audiobook, general TTS and voice-cloning **product workflows are unconditionally `OUT_OF_SCOPE`**. They must not be classified `DONOR_ONLY`, become Genre_test navigation, or enter release milestones. Only the separately named bounded technical primitives may carry `DONOR_ONLY`.

## Acceptance

A donor component can enter production only when:

1. exact source identity is pinned;
2. `product_fit` and `classification` are explicit;
3. target Genre_test owner is explicit;
4. code/model/data rights are separately understood where applicable;
5. hidden download/network/runtime behavior is excluded or documented;
6. deterministic tests/evidence exist;
7. Audio Science is run when audio/listening/DSP semantics change;
8. normal QA/MTD gates pass.

The donor intake record is engineering evidence, not release authority.
