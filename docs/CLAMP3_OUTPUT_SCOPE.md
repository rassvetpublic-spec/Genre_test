# CLaMP 3 / v0.5 output scope

This document records which richer analysis ideas are **in scope now** and which remain in `FAR_TODO.md`.

## In v0.5 scope

### A. Core Sound / deterministic description

Purpose:

- human-readable summary of the track;
- better SUNO-facing compact output;
- better search-result explanation;
- deterministic, evidence-aware wording.

Inputs may include only versioned evidence already available from:

- Genre/Family/Secondary/Adjacent;
- BPM/key;
- AST moods/instruments/production;
- validated CLaMP zero-shot descriptors when they graduate;
- temporal structure outputs when available.

Rules:

- no LLM required for baseline;
- no invented facts;
- every phrase must map to known evidence or a documented template rule;
- output versioned separately from raw analysis.

Example target:

```text
Core sound:
Dark high-energy electronic track centered on Dubstep,
with Drum n Bass influence, heavy electronic percussion
and a driving modern production character.
```

### B. Tempo / Structure Map

Purpose:

- avoid pretending a multi-tempo or beat-switch track has only one global BPM;
- expose strong section/change points;
- connect retrieval segments to musical structure.

Initial output:

```text
Global tempo: 115 BPM
Tempo confidence: medium

Tempo map:
00:00–01:02  ~115 BPM
01:02–01:05  transition
01:05–02:15  ~140 BPM

Structure change:
01:03  significant rhythmic/tempo change
```

Rules:

- section labels such as Verse/Chorus are not required in v0.5;
- transition type such as `tape stop` is not a fact unless separately supported;
- segment-level tempo estimates carry confidence/ambiguity;
- current tempo-v2 global output remains available for compatibility.

### C. Experimental controlled descriptors

Issue #37 may benchmark:

- mood;
- character;
- movement/groove;
- energy bands;
- small vocal-presence/style vocabulary;
- production era/decade.

These remain experimental until reviewed/calibrated.

## Explicitly not required for v0.5

Stored in [`FAR_TODO.md`](FAR_TODO.md):

- rich vocal register/timbre/diction/spatial profile;
- event-level kick/snare/hat/808 decomposition;
- detailed production/mastering profile;
- plug-in/processor inference;
- creative arrangement advice;
- full Verse/Chorus/Drop structure naming;
- detailed motif/transcription outputs;
- AI-music origin detection;
- million-track ANN infrastructure;
- cloud/external catalog integrations.

## Product truth rule

Genre_test outputs are separated into:

```text
MEASURED / MODEL EVIDENCE
    ↓
RESOLVED ANALYSIS
    ↓
DETERMINISTIC DESCRIPTION
    ↓
OPTIONAL CREATIVE RECOMMENDATIONS (future)
```

A lower layer may summarize an upper layer, but it must not be mistaken for new evidence.
