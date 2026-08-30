# TemporalStructureProfile v1

Status: research prototype  
Owner phase: v0.6 Repair & Stem Lab  
Issue: #137  
Related: #45, #50, #54, #63

## Purpose

`TemporalStructureProfileV1` is a backend-neutral, deterministic measurement bundle for
short-time timbral motion, onset timing and transient diversity. It also exposes a conservative
periodic spectral-peak research metric.

The profile is **not** an AI-origin classifier. No field proves that audio is AI-generated,
human-made, SUNO-produced, or produced by any other named generator. Values are evidence for
corpus research and before/after repair comparison only.

## Research evidence chain

External literature and code references are pinned in:

```text
docs/TEMPORAL_STRUCTURE_SOURCES.md
```

Project-owned evidence must then follow the staged protocol in:

```text
docs/TEMPORAL_STRUCTURE_RESEARCH_PIPELINE.md
```

Canonical sequence:

```text
literature/source claim
    -> corpus benchmark
    -> feature distributions
    -> calibration
    -> locked validation
    -> repair validation
```

The extractor being implemented does not imply that later stages are complete. Until corpus measurements exist, distribution/calibration state must be recorded as `NOT_MEASURED` / `NOT_STARTED`, never replaced by assumed detector percentages.

## Implementation

Module:

```text
src/genre_test/technical/temporal_structure.py
```

Public entry point:

```python
analyze_temporal_structure(audio, sample_rate_hz, config=None)
```

Algorithm identity:

```text
genre-test-temporal-structure/1
```

The module accepts mono PCM and 2-D channels-first/channels-last arrays. It does not modify the
source and is not wired into ordinary Analyze, MAEST, AST or CLaMP execution.

## Contract

```json
{
  "schema": "temporal-structure-profile/1",
  "algorithm_identity": "genre-test-temporal-structure/1",
  "sample_rate_hz": 48000,
  "duration_s": 0.0,
  "status": "OK",
  "mfcc": {},
  "rhythm": {},
  "transients": {},
  "spectral_artifacts": {},
  "configuration": {}
}
```

Every interpretation must retain the configuration and algorithm identity. Cross-build
comparisons are invalid when algorithm/configuration identity differs unless explicitly treated
as method drift.

## MFCC temporal dynamics

Fields:

- `mfcc_delta_variance` — mean variance of first-order MFCC temporal derivatives;
- `mfcc_delta2_variance` — mean variance of second-order derivatives;
- `mfcc_trajectory_path_length` — mean Euclidean frame-to-frame MFCC step;
- `mfcc_trajectory_acceleration_p95` — 95th percentile norm of second-order MFCC motion.

These describe timbral motion. MFCC presence is not generator evidence, and these values must not
be called an AI score.

## Rhythm / microtiming

Fields:

- `onset_count`;
- `tempo_bpm`;
- `onset_grid_deviation_ms_median`;
- `onset_grid_deviation_ms_iqr`;
- `inter_onset_interval_cv`;
- `beat_locked_onset_ratio`.

The current research grid uses the estimated global tempo and four subdivisions per beat by
default. Results inherit onset/tempo-estimation uncertainty and must be compared by distributions,
not universal thresholds.

Hard-negative material is mandatory: fully human DAW productions with hard quantization, drum
machines, repeated loops and sample reuse can naturally produce highly regular timing.

## Transient diversity

Fields:

- `transient_count`;
- `attack_similarity_median`;
- `attack_similarity_p95`;
- `attack_energy_cv`;
- `attack_time_cv`;
- `spectral_flux_cv`.

Attack similarity is computed from normalized short attack log-mel vectors. It measures acoustic
similarity between detected attacks; it does not establish whether repeated attacks came from a
sampler, drum machine, human edit, generator or live performance.

## Periodic spectral-peak research metric

Fields:

- `periodic_peak_score`;
- `peak_spacing_hz`;
- `peak_persistence`;
- `candidate_peak_count`.

This is an exploratory measurement of regular narrow spectral-peak structure above the configured
minimum frequency. It is intentionally not named `generator_fingerprint` and must not be used as
provenance truth without a separately designed and validated classifier project.

## Mapping to TechnicalProfile / GenerativeDefectProfile

The profile can be embedded as a versioned extension of future `TechnicalProfileOutputV1`:

```text
TechnicalProfileOutputV1.extensions.temporal_structure
    -> TemporalStructureProfileV1
```

It may supply evidence to `GenerativeDefectProfileV1` only after corpus calibration and reviewed
listening confirms that a signal pattern corresponds to an audible defect.

Candidate reviewed defect labels after calibration:

- `TRANSIENT_REPETITION`;
- `RHYTHMIC_MECHANICALITY`;
- `TEMPORAL_TIMBRE_ANOMALY`;
- `PERIODIC_SPECTRAL_ARTIFACT`.

They are not promoted by this prototype. A metric anomaly is not automatically a defect.

## Benchmark gate

Minimum corpus matrix before interpretive thresholds are allowed:

1. raw SUNO fixtures;
2. other generator families where reproducible/legal fixtures exist;
3. live human performance;
4. human DAW production with hard quantization;
5. drum-machine and loop-heavy human production;
6. human tracks after limiting/mastering/MP3/AAC;
7. generated tracks raw vs mastered vs codec vs stem-recombined;
8. clean and deliberately degraded controls.

Report distributions, overlap, false-positive behaviour, genre sensitivity and processing
sensitivity. Do not publish a universal `AI/HUMAN` threshold from one corpus.

Detailed parent-family splitting, duration axes, distribution statistics, calibration records, locked-test rules and repair-validation gates are defined in `TEMPORAL_STRUCTURE_RESEARCH_PIPELINE.md`.

## Repair use

For a repair candidate, store source and candidate profiles beside existing musical-damage guards.
A change in temporal/spectral evidence is useful only when paired with:

- loudness-matched blind listening;
- transient retention;
- stereo/mono preservation;
- vocal integrity;
- artifact-reduction rating;
- musical-damage rating.

A lower artifact-evidence value alone must never select a repair winner.

## Failure and scope rules

- invalid/empty/non-finite audio fails explicitly;
- missing onsets produce `None` for unavailable rhythm/transient measurements rather than guessed values;
- source PCM is immutable;
- no detector-score minimization objective;
- no watermark/provenance stripping;
- no generator attribution from these metrics;
- ordinary Analyze remains unchanged.

## v1 prototype acceptance

- deterministic MFCC temporal group;
- deterministic onset/microtiming group;
- deterministic transient-diversity group;
- exploratory periodic spectral-peak group;
- synthetic positive/negative behaviour tests;
- channels-first/channels-last handling;
- explicit invalid-input tests;
- separate algorithm/config identity;
- no AI probability or named-generator output;
- pinned source registry and explicit benchmark/calibration/repair-validation protocol;
- no merge without explicit MTD.
