---
title: "Genre_test Donor Intake Contract"
doc_type: protocol
area: project
status: canonical
summary: "Canonical admission gate for donor technologies: product fit, provenance, authority boundaries, evidence class and acceptance before any port/adaptation."
tags:
  - область/project
  - тип/protocol
  - статус/canonical
---

# Genre_test Donor Intake Contract

Tracking origin: **#200**

## Purpose

A donor repository, prototype, paper implementation or owner-supplied archive is an input to engineering review. It is never a roadmap owner and never becomes a second source of product/runtime truth merely because useful code or UX exists there.

Every donor component must map to an existing in-scope Genre_test job/Issue before implementation.

## Required admission record

Use this minimum record for each donor component considered for production integration:

```yaml
donor_id: <stable donor identifier>
donor_revision: <exact commit/hash/archive identity>
donor_path: <exact file/module/component path>
product_fit: IN_SCOPE | DONOR_ONLY | OUT_OF_SCOPE
classification: PORT | ADAPT | REIMPLEMENT | EXPERIMENT | REJECT
owner_issue: <Genre_test Issue>
target_owner: <Genre_test canonical subsystem/contract>
evidence_class: <source/runtime/research/UX evidence class>
license_provenance: <code rights / model-weight rights / unknown>
network_or_download_behavior: <explicit>
runtime_isolation: <explicit>
acceptance_gate: <tests/review/science gate>
```

Missing exact source identity prevents direct `PORT`/`ADAPT` claims. Changelog-only or prose-only behavior is a requirement/reference and must be `REIMPLEMENT` or `EXPERIMENT` until recoverable source is pinned.

## `product_fit` meanings

### `IN_SCOPE`

The donor component directly implements or accelerates an already accepted Genre_test product capability:

- music analysis/catalog/retrieval;
- Technical QC;
- generative-song/stem/vocal repair;
- studio-finish/mastering and controlled comparison;
- AI-origin/provenance detector research/evidence;
- runtime/research/delivery infrastructure required by those capabilities.

`IN_SCOPE` still requires provenance, architecture ownership and acceptance evidence.

### `DONOR_ONLY`

The originating product feature itself is outside Genre_test, but a bounded technical primitive may be useful for an in-scope capability.

Examples:

- subprocess/process-tree containment from a speech production tool;
- device/provider diagnostics;
- phrase/activity alignment used only as evidence;
- UX layout patterns;
- controlled synthetic fixture generation for research.

Only the bounded primitive is admitted. The donor product workflow is not.

### `OUT_OF_SCOPE`

The component maps to a product family Genre_test explicitly does not implement:

- dubbing pipeline;
- audiobook production pipeline;
- general-purpose TTS studio;
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

Issue #199 may admit runtime/operations primitives from VoiceStudio, such as process containment, capability truth, doctor/deep-doctor patterns and heartbeat/liveness.

VoiceStudio dubbing, audiobook, general TTS and voice-cloning product workflows remain `OUT_OF_SCOPE` or `DONOR_ONLY` as appropriate and must not become Genre_test navigation or release milestones.

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
