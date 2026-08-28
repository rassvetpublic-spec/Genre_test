# Generative Audio Repair Source Registry — Addendum 2026-08-28

Status: **REFERENCE ADDENDUM**  
This extends `GENERATIVE_AUDIO_REPAIR_SOURCE_REGISTRY.md`; it does not replace its evidence-ranking rules.

## Primary/vendor context

| Source | What it supports | What it does not support |
|---|---|---|
| Suno v5.5 release notes/blog | product claim that v5.5 targets richer arrangements, sharper vocals and more dynamic sound | prevalence of any defect or a detector threshold |
| iZotope Ozone 12 / Unlimiter documentation | prior limiting can be treated as a distinct restore problem; restoration should be conditional on evidence | a universal Suno mastering chain |
| iZotope mastering workflow | useful causal distinction between low-end attack/body, Bass Control and subsequent dynamics | fixed settings for generated audio |
| iZotope T/S imaging guidance | transient placement can be preserved while ambience/body is widened | permission to widen every generated master |

References:

- https://suno.com/release-notes/introducing-v5-5-voices-custom-models-and-my-taste
- https://www.izotope.com/community/blog/inside-ozone-12
- https://www.izotope.com/community/blog/how-to-master-a-song-from-start-to-finish
- https://www.izotope.com/community/blog/advanced-mastering-tips

## Community implementation references

### `TheApeMachine/deshimmer`

Reference: https://github.com/TheApeMachine/deshimmer

Transferable engineering ideas:

- transient/energy-flux protection around legitimate attacks;
- spectral/tonal gates rather than blind static high-frequency removal;
- stereo/phase-aware cleanup and optional HF decorrelation concepts;
- inspect musical leakage/damage, not only artifact score.

Boundary: community implementation, not ground truth and not a universal frequency prescription.

### `henricksmedia/shimmer`

Reference: https://github.com/henricksmedia/shimmer

Transferable engineering ideas:

- Suno-oriented high-frequency cleanup as a measurable repair route;
- transient protection;
- Mid/Side differentiated cleanup in its own design.

Boundary: fixed bands/strengths from the project are implementation choices, not Genre_test defaults.

## Community Suno v5.5 reports

Recurring reports mention some combination of:

- metallic/sibilant high-frequency texture;
- hiss/crackle around hats/vocals;
- low-mid thinning;
- softened/flattened transients;
- phase smear or stereo instability.

Use only for fixture discovery and taxonomy coverage. Do not infer that every v5.5 render contains these symptoms.

## New registry rule

Any source proposing a repair target must be separated into:

```text
symptom evidence
mechanism hypothesis
implementation choice
validated benchmark result
```

Only the last category may promote a repair route toward `SAFE`. A popular forum frequency range is never sufficient by itself.
