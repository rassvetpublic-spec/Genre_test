# ADR-0004: Raw Evidence, Resolved Profile and Presentation Are Separate Layers

Status: **accepted**

## Context

Genre_test combines MAEST, AudioSet AST and DSP measurements and exposes Normal, SUNO and Distributor interpretations. Conflating these layers would make validation and regressions ambiguous.

## Decision

Maintain separate layers:

```text
raw model/DSP evidence
 -> deterministic resolved AudioProfile
 -> presentation projection (Normal/SUNO/Distributor)
 -> optional mastering hypothesis
 -> rendered/validated mastering winner
```

Raw MAEST validation remains available independently of product-layer fusion.

Source metadata is also separate from internal resampled analysis-stream properties.

## Consequences

- Presentation can change without re-running models.
- A SUNO or Distributor view cannot mutate classifier evidence.
- Mastering decisions cannot overwrite the original classification record.
- Source bitrate/sample rate cannot be derived from the model input stream.

## Validation

Tests should compare raw evidence, profile resolution and presentation output independently.
