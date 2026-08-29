# ADR-0003: Mastering Validation Guards

Status: **accepted**

## Context

Loudness, stereo width and artifact suppression can improve one metric while damaging attack, mono compatibility or codec translation.

## Decision

Mastering candidates are evaluated against reusable guards:

1. technical integrity / XML / export format;
2. loudness-matched musical A/B;
3. event-aligned transient attack;
4. mono retention overall/event/by band;
5. Side/Mid behavior where relevant;
6. true/sample peak;
7. real MP3/AAC encode -> decode audit for final delivery;
8. duration/padding/tail integrity.

Hard reject examples include important mono disappearance and audible drum/punch destruction.

Legacy numerical thresholds are heuristics, not universal truth.

## Consequences

A wider/louder/cleaner candidate can lose even when its headline metric improves.

The validation layer must preserve raw measurements so thresholds can be changed without losing evidence.

## Validation

See `docs/VALIDATION_KNOWLEDGE.md` and the archived Universal Core automatic mastering meter specification.
