# ADR-0002: Ozone 12 Backend and Problem-Driven Stage Model

Status: **accepted**

## Context

The legacy mastering lab validated a repeatable Ozone 12 workflow and a full module-slot topology. A topology can be useful while an always-on preset is unsafe across different tracks.

## Decision

- Ozone 12 Advanced remains the mastering backend inside Genre_test.
- REAPER is the reproducible render host.
- The 16-slot sequence is an order/topology contract, not an always-on chain.
- `BYPASS` is a valid winner for every module.
- Each active module must have a unique measured/audible job.
- Stage changes should be one problem/one main axis at a time.
- The selected current winner becomes the next base.
- Active Ozone chain membership is read from `ElementChain`.
- Unknown/build-sensitive XML mappings are not automated without calibration evidence.

## Consequences

Genre/profile labels may propose mastering hypotheses but cannot activate modules by themselves.

Automation must preserve prior accepted XML blocks and unknown data outside the declared stage scope.

## Validation

A stage is accepted only after loudness-matched listening plus the relevant technical guards defined in `docs/VALIDATION_KNOWLEDGE.md`.
