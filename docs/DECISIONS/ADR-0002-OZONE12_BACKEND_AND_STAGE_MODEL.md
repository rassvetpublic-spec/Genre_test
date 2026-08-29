# ADR-0002: Ozone 12 Backend and Problem-Driven Stage Model

Status: **accepted**

## Context

The legacy mastering lab validated a repeatable Ozone 12 workflow and a full module-slot topology. A topology can be useful while an always-on preset is unsafe across different tracks.

## Decision

- Ozone 12 Advanced remains an **optional mastering backend** inside Genre_test; ordinary analysis, catalog/search/retrieval, validation, and non-Ozone workflows must not require Ozone to be installed or available.
- When the Ozone backend is selected, REAPER is the reproducible render host.
- The 16-slot sequence is an order/topology contract for that backend, not an always-on chain.
- `BYPASS` is a valid winner for every module.
- Each active module must have a unique measured/audible job.
- Stage changes should be one problem/one main axis at a time.
- The selected current winner becomes the next base.
- Active Ozone chain membership is read from `ElementChain`.
- Unknown/build-sensitive XML mappings are not automated without calibration evidence.

## Consequences

Genre/profile labels may propose mastering hypotheses but cannot activate modules by themselves.

Ozone integration cannot become a startup/runtime dependency of ordinary analysis or retrieval. Backend selection remains explicit, and non-Ozone mastering backends may coexist under the canonical mastering-backend boundary.

Automation for the Ozone backend must preserve prior accepted XML blocks and unknown data outside the declared stage scope.

## Validation

An Ozone stage is accepted only after loudness-matched listening plus the relevant technical guards defined in `docs/VALIDATION_KNOWLEDGE.md`.
