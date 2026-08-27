# Generative Audio Repair Lab — benchmark specification

Status: design specification  
Related: #45, #50, #52, #54, #63

## Goal

Build a reviewed corpus of **50–100 real SUNO excerpts** and clean controls to compare Apollo, A2SB, conventional DSP and stem-assisted repair objectively and by controlled listening.

This benchmark is independent from the Ozone mastering chain. Ozone/REAPER candidates may be consumed later by #54, but repair backends are evaluated before mastering and at matched loudness.

## Corpus size and composition

Target v1: **80 primary excerpts**, 6–20 seconds each.

| Group | Target | Purpose |
|---|---:|---|
| Metallic/harsh high-frequency texture | 12 | cymbals, dense choruses, synthetic sheen |
| Vocal sibilance/consonant/crackle defects | 12 | identity-sensitive vocal repair |
| Warble/zipper/spectral instability | 10 | neural/codec-like modulation |
| Clicks, discontinuities, local clipping | 8 | deterministic DSP and inpainting |
| Transient smear/weak attacks | 10 | drums and percussive material |
| Phase smear/mono loss/stereo instability | 8 | stereo safety |
| Spectral holes/bandwidth collapse | 8 | Apollo/A2SB eligibility |
| Stem leakage/musical noise | 6 | separator/recombination safeguards |
| Clean/acceptable controls | 6 | false-positive and over-processing guards |
| **Total** | **80** | expandable to 100 after pilot |

Balance where possible across sparse/dense arrangement, male/female vocals, acoustic/electronic sources, low/high energy and multiple generation versions. The corpus is not intended to estimate prevalence across all SUNO output.

## Storage model

Real user-owned SUNO audio remains outside public Git unless redistribution rights are explicit.

Repository stores:

- corpus manifest;
- excerpt SHA-256 and parent-file SHA-256;
- local relative locator template, never a private absolute path;
- timestamps;
- technical metadata;
- user-provided generator/version when known;
- annotation JSON;
- split assignment;
- license/redistribution state;
- optional synthetic/redistributable fixtures.

Recommended local root:

```text
.genre_test/benchmarks/generative_repair_v1/
  audio/
  annotations/
  renders/
  reports/
```

Git tracks schemas, manifests without private paths, scripts and small redistributable fixtures only.

## Annotation protocol

Each excerpt is independently reviewed by at least two listeners.

Pass 1:

- blind listen at calibrated fixed playback level;
- mark audible interval;
- select defect type and scope;
- severity: NOTICE/MINOR/MAJOR/CRITICAL;
- confidence: LOW/MEDIUM/HIGH;
- short audible description.

Pass 2:

- inspect waveform/spectrogram and technical markers;
- confirm, reject or mark ambiguous;
- identify likely repair route without seeing candidate identity.

Disagreement:

- exact interval overlap target: intersection-over-union >= 0.3 for event defects;
- taxonomy agreement reported with Cohen's kappa or raw agreement when sample count is insufficient;
- disagreements adjudicated by a third review or retained as AMBIGUOUS;
- training/calibration data and final test data remain separate.

## Dataset splits

- `pilot`: 10 excerpts for tooling and threshold development;
- `calibration`: 30 excerpts for detector/backend settings;
- `test`: 30 excerpts locked before final comparison;
- `challenge`: 10 difficult/ambiguous excerpts, reported separately.

No tuning on locked test audio. Track/source families must not cross splits.

## Candidate matrix

Every eligible excerpt keeps `R0 ORIGINAL`.

Required baselines:

- `D1 DSP_SAFE`: bounded deterministic de-click/de-harsh/phase or transient repair appropriate to the label;
- `D2 DSP_PROBE`: wider boundary probe;
- `A1 APOLLO_SAFE`;
- `A2 APOLLO_PROBE`;
- `S1 A2SB_LOCAL` for bandwidth/inpainting-eligible excerpts;
- `T1 STEM_SAFE`: maintained separator plus per-stem repair;
- `T2 STEM_ENSEMBLE_PROBE` where two model families disagree;
- optional `N0 NO_ACTION` decision.

Inapplicable candidates are `N/A`, not zero-quality failures. Exact backend/checkpoint availability remains license- and runtime-gated.

## Processing rules

- immutable original;
- pinned code revision and checkpoint SHA-256;
- model/code license recorded separately;
- deterministic seed and tolerance where possible;
- output aligned to source;
- no normalization before analysis except explicit loudness-matched listening copies;
- processing manifest for every candidate;
- no automatic Ozone/mastering chain inside benchmark;
- Safe/Probe/Refine settings bounded and versioned;
- failed backend remains a recorded failure, not silent fallback.

## Objective measurements

Source and candidate:

- LUFS-I, short-term loudness, LRA, sample peak and true peak;
- crest/PLR and transient attack-to-sustain retention;
- clipped runs, discontinuities, NaN/silence/gain anomalies;
- spectral delta by bands and spectral-cutoff evidence;
- high-band tonality/flatness and temporal instability;
- mid/side energy, bandwise correlation, mono-loss estimate;
- local marker precision/recall against reviewed intervals;
- chunk-boundary continuity;
- runtime, VRAM, RAM, load/warm time and real-time factor.

Stem routes additionally:

- mixture reconstruction residual;
- latency/alignment;
- stem leakage/musical-noise markers;
- recombined full-mix damage;
- model disagreement.

Analyzer robustness, reported separately:

- MAEST family/Top-K changes;
- AudioSet AST tag changes;
- BPM/key stability;
- CLaMP cosine and neighbour overlap;
- label `ROBUSTNESS AXIS: SOURCE_RESTORATION`, never analyzer-build `DRIFT`.

## Listening evaluation

Use #54 synchronized A/B/X infrastructure when available; pilot may use an equivalent reproducible local session.

Requirements:

- time-aligned instant switching;
- hidden candidate identity and randomized order;
- loudness matching with applied gain logged;
- repeated anchor/control;
- fixed loop around defect plus context;
- headphones and speaker/mono check for relevant cases.

Separate 1–5 ratings:

- artifact reduction;
- musical damage;
- vocal identity/timbre preservation;
- transient preservation;
- stereo/mono preservation;
- overall preference.

Primary success criterion is not preference alone:

```text
artifact reduction improves
AND musical damage stays below gate
AND hard technical guards pass
```

## Metrics and ranking

Report per defect group and overall:

- confirmed-marker precision/recall for detectors;
- pairwise win/loss/tie versus original;
- mean/median artifact-reduction score;
- musical-damage rejection rate;
- hard-failure rate;
- over-processing rate on clean controls;
- runtime/resource cost;
- bootstrap confidence intervals where sample size permits.

Do not collapse all results into one universal score. Publish a route recommendation matrix by defect class.

## Graduation gates

A backend can become `SAFE` only when:

- provenance and licenses are explicit;
- Windows Python 3.12 / Torch cu130 / RTX 5070 Ti smoke passes where GPU is required;
- no silent source mutation;
- repeatability tolerance documented;
- clean-control over-processing rate is acceptable;
- no critical stereo, transient, vocal-identity or chunk-boundary failures;
- it beats original or DSP baseline on its eligible defect class under blind review;
- failure/cancel/unload behavior is verified.

Otherwise it remains `PROBE_ONLY`, `EXPERIMENTAL` or `REJECTED`.

## Deliverables

- `GenerativeDefectProfileV1` JSON Schema/Pydantic model;
- corpus manifest schema and validator;
- annotation guide and reviewer form;
- private-local corpus bootstrap script;
- candidate processing manifests;
- objective CSV/JSON reports;
- #54 comparison sessions;
- benchmark report with per-defect recommendations;
- license/runtime audit for every tested backend.
