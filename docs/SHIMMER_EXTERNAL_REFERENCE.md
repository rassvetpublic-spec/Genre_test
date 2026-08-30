# Shimmer external reference for Genre_test

Status: **external R&D reference / test candidate; not production truth**  
Snapshot date: **2026-08-30**  
Relevant areas: AI-audio artifact cleanup, pre-master repair, delta/removed audition, loudness-matched A/B, transient preservation, Mid/Side high-band cleanup

## Purpose

Shimmer is recorded here as an external open-source reference implementation and experiment source for cleanup of artifacts associated with AI-generated music, especially Suno/Udio material.

It may be used to:

- generate hypotheses for `Genre_test` repair research;
- benchmark cleanup behavior on controlled fixtures;
- compare before/after/delta listening workflows;
- inspect artifact-detection and safety-gate ideas;
- provide an external reference when designing project-owned DSP experiments.

It must **not** become authoritative evidence that a specific artifact exists, and its processing decisions must not silently become `Genre_test` production defaults.

Recommended role:

```text
EXTERNAL_REFERENCE / TEST_CANDIDATE / DSP_HYPOTHESIS_SOURCE
```

Not:

```text
PRODUCTION_TRUTH / REQUIRED_DEPENDENCY / AUTOMATIC_REPAIR_DEFAULT
```

## Primary source

Repository:  
https://github.com/henricksmedia/shimmer

Verified on 2026-08-30.

The project describes itself as a local/offline suite for cleaning artifacts from AI-generated music before mastering. Its public documentation states that cleanup precedes mastering, and that the cleanup path uses deterministic classic DSP rather than machine learning.

## High-value ideas for Genre_test

### 1. Cleanup before mastering

Shimmer explicitly separates artifact removal from mastering and performs cleanup first.

This is a useful hypothesis for `Genre_test` because compression, excitation, tone shaping and limiting can make high-frequency fizz, metallic ringing or unstable cymbal/vocal texture more obvious after mastering.

Candidate project architecture:

```text
artifact analysis
  -> bypass | repair candidate
  -> repair QC
  -> normal mastering chain
  -> final limiter / codec audit
```

`bypass` must remain a valid winner.

### 2. Removed / Delta audition

Shimmer exposes the removed signal as a separate audition path. Its documentation recommends lowering processing strength when vocals, snare hits, melody or other wanted material becomes audible in the removed signal.

This is directly applicable as a conservative QC gate.

Recommended fixture outputs:

```text
original.wav
processed.wav
removed_delta.wav
```

Recommended review questions:

- Does the delta contain primarily unwanted noise/artifact energy?
- Are vocal formants, melody, cymbal body or drum attacks clearly present?
- Is transient material being removed disproportionately?
- Does the processed version still win after loudness matching?

If wanted musical content is clearly present in the delta, the repair candidate should be penalized or rejected.

### 3. Loudness-matched A/B

Shimmer enables loudness-matched comparison between versions to reduce preference bias toward the louder render.

`Genre_test` should use the same principle for any repair experiment:

```text
original vs repair candidate
  -> loudness match
  -> blind or minimally biased listening comparison
  -> objective QC metrics
```

Do not accept a repair candidate solely because it is louder, brighter or more limited.

### 4. High-band-only processing

Shimmer documents a crossover around 4.5 kHz so low-frequency and much of the vocal/body region bypass the artifact-cleanup engine.

This should be treated as a testable design hypothesis, not a universal cutoff.

Candidate experiment:

- test several crossover regions;
- compare full-band cleanup vs high-band-only cleanup;
- measure low/mid-band collateral change;
- inspect delta spectrogram and transient retention;
- evaluate genre-dependent behavior.

### 5. Mid/Side asymmetry

Above the crossover, Shimmer processes Mid and Side differently, with stronger protection of the center and more aggressive cleanup in the sides.

This is relevant for generated material where wide synthetic ambience, cymbal wash or stereo high-frequency texture may contain stronger artifacts than the center channel.

Candidate test matrix:

```text
A: stereo-linked cleanup
B: high-band M/S cleanup, equal strength
C: protected Mid + stronger Side
D: bypass
```

Evaluate:

- vocal/snare integrity;
- stereo width;
- mono compatibility;
- HF artifact reduction;
- removed-signal contamination.

### 6. Transient safety gate

Shimmer documents a transient-protection gate that backs off cleanup for roughly 70 ms around detected transients.

This maps well to `Genre_test` transient/sustain QC.

Project-owned tests should vary:

- transient detector sensitivity;
- release/protection time;
- attenuation depth during the gate;
- genre and drum-density conditions.

The exact Shimmer value is a reference point only, not a required project constant.

### 7. Artifact-specific preset analysis

Shimmer exposes multiple artifact presets and an analyzer that selects among them.

The useful research idea is not the preset list itself, but the separation of artifact families such as:

- broadband fizz/hash;
- cymbal sheen/chatter;
- ringing/whistle-like tones;
- vocal glaze/sibilance instability;
- harshness/fatigue;
- muddy/boxy rescue cases.

`Genre_test` can use these as candidate labels for listening fixtures and detector research, while keeping project-owned definitions and validation.

## Recommended test protocol

For each selected AI-generated test track:

```text
1. Preserve untouched source.
2. Select artifact-heavy and artifact-light excerpts.
3. Produce bypass and one or more repair candidates.
4. Loudness-match candidates for review.
5. Export removed/delta signal for every candidate.
6. Run transient-retention and spectral-difference metrics.
7. Run mono and codec audit where relevant.
8. Perform human review.
9. Accept repair only if it beats bypass without unacceptable collateral damage.
```

Suggested objective evidence:

- integrated and short-term loudness before/after matching;
- true peak;
- spectral delta by frequency band;
- Mid/Side spectral delta;
- transient peak/crest retention;
- correlation / mono compatibility;
- codec re-encode audit;
- artifact-region vs clean-region differential behavior.

## Explicit non-goals

- Do not copy Shimmer DSP code directly into `Genre_test`.
- Do not make Shimmer a required runtime dependency.
- Do not assume all Suno/Udio tracks need repair.
- Do not apply a universal high-frequency cut.
- Do not treat 4.5 kHz or 70 ms as validated `Genre_test` constants.
- Do not accept automated artifact detection as ground truth without listening and project-owned evidence.
- Do not let repair overwrite the untouched source.
- Do not make a processed candidate win by default; bypass remains eligible.

## Source and implementation boundary

Shimmer is released under AGPL-3.0. For `Genre_test`, the preferred use is as an external source of information, a comparison tool and a generator of independently testable DSP hypotheses.

If an idea is adopted, it should be re-derived and implemented from project-owned requirements and tests rather than copied from Shimmer source code.

## Recommended priority

1. Removed/Delta audition as mandatory repair QC.
2. Loudness-matched A/B for repair evaluation.
3. Cleanup-before-mastering experiment.
4. High-band-only repair experiment.
5. Protected-Mid / stronger-Side experiment.
6. Transient safety gate experiment.
7. Artifact-family detector taxonomy research.
8. Full Shimmer-vs-Genre_test benchmark on reviewed fixtures.

## Engineering conclusion

Shimmer is high-value for `Genre_test` as an **external repair reference and controlled test candidate**. The strongest transferable value is its evaluation methodology: cleanup before mastering, explicit removed-signal audition, loudness-matched comparison, spatially selective high-band processing and transient protection.

These ideas should enter `Genre_test` as hypotheses to validate experimentally, while the project remains source-independent and keeps bypass/original audio as a valid outcome.