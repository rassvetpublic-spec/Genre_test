# TemporalStructureProfile research pipeline

Status: research/benchmark protocol  
Issue: #137  
Related: #45, #50, #54, #63  
Inputs: `TEMPORAL_STRUCTURE_PROFILE.md`, `TEMPORAL_STRUCTURE_SOURCES.md`, `GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`

## Goal

Turn external hypotheses and `TemporalStructureProfileV1` measurements into project-owned evidence through a fixed sequence:

```text
literature / source claim
    -> corpus benchmark
    -> feature distributions
    -> calibration
    -> locked validation
    -> repair validation
    -> optional promoted defect evidence
```

No stage may be skipped. In particular, an interesting external detector result, single track, screenshot, or correlation must not become a threshold or repair rule directly.

## 1. Literature/source intake

All external claims relevant to MFCC dynamics, microtiming, transient repetition, long-range structure or spectral artifacts are entered in `TEMPORAL_STRUCTURE_SOURCES.md`.

For each source record:

- stable paper identifier/version;
- official URL;
- official code URL when available;
- pinned commit SHA when inspected/executed;
- dataset identity when relevant;
- claim supported by the source;
- explicit non-claim / transfer limitation;
- project experiment motivated by the source.

A source can create an experiment. It cannot directly create a production threshold.

## 2. Corpus benchmark

### 2.1 Unit of independence

The split unit is the **parent/anchor song family**, not an arbitrary excerpt. All variants derived from the same source stay in the same split.

Examples of one family:

```text
track_A_original.wav
track_A_limited.wav
track_A_mp3_320.mp3
track_A_aac.m4a
track_A_pitch_plus_1.wav
track_A_stem_recombined.wav
```

This prevents processing variants of the same musical content from leaking across calibration and locked test data.

### 2.2 Minimum corpus families

The temporal-structure benchmark must contain all applicable groups below before any interpretive threshold is promoted.

| Family | Required role | Key confound controlled |
|---|---|---|
| Raw generated music | positive research family, generator known only from provenance | generator output before project processing |
| Multiple generator families | generator-held-out validation | overfitting to one service/model |
| Human live/performed music | negative/control family | natural timing/timbre variation |
| Human DAW, hard quantized | hard negative | grid precision is not generator-specific |
| Human drum-machine/sample-loop production | hard negative | transient repetition is not generator-specific |
| Human autotuned/heavily edited production | hard negative | aggressive production artifacts |
| Human limited/mastered variants | processing hard negative | mastering-induced spectral/transient change |
| Human MP3/AAC variants | codec hard negative | codec-induced high-band/spectral structure |
| Generated mastered variants | processing robustness | evidence stability after mastering |
| Generated MP3/AAC variants | codec robustness | evidence stability after distribution codec |
| Generated stem-recombined variants | pipeline robustness | separator/recombination artifacts |
| Clean/acceptable controls | over-processing guard | avoid inventing defects |
| Deliberately degraded controls | sensitivity sanity check | known perturbation response |

### 2.3 Generator metadata

Generator/service/model/version is **provenance metadata only** and must never be inferred from `TemporalStructureProfileV1`.

Record when known:

```text
generator_family
generator_service
generator_model_or_version
creation_date_or_window
source_prompt_hash_or_private_reference (optional)
provenance_confidence = KNOWN | USER_REPORTED | UNKNOWN
```

Unknown provenance remains `UNKNOWN`; do not guess it from audio.

### 2.4 Segment durations

At minimum evaluate the same parent family at multiple durations where source length permits:

- 5 s;
- 10 s;
- 30 s;
- 60 s;
- full selected region / full track where computationally practical.

Duration is part of the benchmark condition because onset/tempo and distribution stability can change with excerpt length.

### 2.5 Recommended split

For a first project-owned corpus large enough for calibration:

```text
pilot        10–15%  tooling only
calibration  35–40%  threshold/model development
validation   20–25%  model/feature selection check
locked_test  20–25%  final report, never tuned on
challenge     optional difficult/ambiguous families reported separately
```

If the corpus is too small to support these partitions, the result remains `PILOT_ONLY`; do not compensate by reusing locked data for tuning.

### 2.6 Storage and privacy

Private/user-owned audio remains outside Git unless redistribution rights are explicit.

Git stores:

- manifest/schema;
- SHA-256 hashes;
- relative locator templates, never private absolute paths;
- split assignments;
- source/provenance metadata;
- processing recipe identity;
- metrics/results;
- small redistributable synthetic fixtures.

Suggested local root:

```text
.genre_test/benchmarks/temporal_structure_v1/
  audio/
  manifests/
  profiles/
  distributions/
  calibration/
  repair_validation/
  reports/
```

## 3. Measurement extraction

Run the same pinned `TemporalStructureProfileV1` algorithm/configuration for every comparable item.

Required identity fields:

```text
schema
genre_test_version
git_commit
algorithm_identity
configuration_hash
runtime_identity
asset_sha256
parent_family_id
variant_id
split
segment_start_s
segment_end_s
duration_s
```

Do not compare values across different algorithm/config identities as though they came from one distribution. A method change creates a new benchmark revision or explicit drift study.

### 3.1 Core feature groups

MFCC temporal:

- `mfcc_delta_variance`;
- `mfcc_delta2_variance`;
- `mfcc_trajectory_path_length`;
- `mfcc_trajectory_acceleration_p95`.

Rhythm/onset:

- `onset_count`;
- `tempo_bpm`;
- `onset_grid_deviation_ms_median`;
- `onset_grid_deviation_ms_iqr`;
- `inter_onset_interval_cv`;
- `beat_locked_onset_ratio`.

Transient diversity:

- `transient_count`;
- `attack_similarity_median`;
- `attack_similarity_p95`;
- `attack_energy_cv`;
- `attack_time_cv`;
- `spectral_flux_cv`.

Spectral artifact research:

- `periodic_peak_score`;
- `peak_spacing_hz`;
- `peak_persistence`;
- `candidate_peak_count`.

## 4. Distribution reports

Raw values come before labels. The primary artifact of the research stage is a set of **distributions**, not one detector percentage.

### 4.1 Required distribution slices

For every promoted metric report, where sample size permits:

- generated vs human;
- each generator family separately;
- human live vs human DAW;
- hard-quantized vs non-hard-quantized human DAW;
- loop/drum-machine vs non-loop controls;
- raw vs mastered;
- lossless vs MP3/AAC;
- raw vs stem-recombined;
- genre/style family;
- vocal/instrumental when known;
- segment-duration bucket;
- loudness/energy bucket where relevant.

### 4.2 Required statistics

Per slice:

```text
n_parent_families
n_segments
missing_or_NA_count
mean
std
median
q05
q25
q75
q95
IQR
MAD
min
max
```

For pairwise comparisons also report, where meaningful:

```text
median_difference
Cliff's_delta or another declared effect size
bootstrap confidence interval
Kolmogorov-Smirnov / Mann-Whitney result only as descriptive evidence
multiple-comparison correction when many hypotheses are tested
```

Statistical significance alone is insufficient. Require effect size, overlap inspection, stability across splits and confound analysis.

### 4.3 Overlap and error view

For any candidate decision boundary, report:

- false-positive rate on all human controls;
- false-positive rate specifically on each hard-negative family;
- false-negative rate per generator family;
- uncertainty/bootstrap interval;
- threshold sensitivity curve;
- duration sensitivity;
- processing sensitivity;
- generator-held-out behaviour.

A threshold that looks good only because hard negatives are absent is invalid.

### 4.4 No invented distributions

Until the corpus is actually measured, repository documentation must say `NOT_MEASURED`, not insert estimated means, assumed percentages, or detector-like numbers.

## 5. Calibration

Calibration converts stable descriptive measurements into versioned **research evidence rules**. It does not automatically create provenance classification.

### 5.1 Promotion prerequisites

A metric may enter calibration only if:

- deterministic fixture tests pass;
- missing/error semantics are explicit;
- sufficient parent-family count exists;
- relevant hard negatives exist;
- distribution plots/tables are available;
- no obvious leakage exists;
- behaviour is not dominated by one genre, loudness range or segment duration;
- the metric has a plausible signal interpretation.

### 5.2 Calibration outputs

Each calibrated metric/rule receives a record:

```text
calibration_id
benchmark_revision
metric_name
algorithm_identity
configuration_hash
calibration_split_hash
eligible_scope
normalization/transformation
candidate_boundary_or_model
selection_objective
hard_negative_constraints
bootstrap_interval
validation_result
known_failure_modes
status = EXPERIMENTAL | PROBE_ONLY | CALIBRATED_RESEARCH
```

Do not use `SAFE` for origin-detection claims. `SAFE` remains a repair/backend concept elsewhere in the project.

### 5.3 Threshold selection rules

If a scalar threshold is evaluated:

1. derive candidates only on `calibration`;
2. select using an explicit objective that penalizes hard-negative false positives;
3. freeze threshold and preprocessing;
4. check once on `validation`;
5. after design freeze, report once on `locked_test`;
6. never retune from locked-test failures without incrementing benchmark/calibration revision and relocking a new test set.

Recommended decision priority for this project:

```text
hard-negative false-positive control
    > generator-family generalization
    > processing robustness
    > aggregate separation score
```

### 5.4 Multi-feature models

If multiple features are fused, store:

- exact feature list/order;
- transforms/normalization;
- model family;
- hyperparameters;
- random seed;
- training split hashes;
- serialized model hash;
- calibration method;
- held-out results.

Feature fusion may be researched, but it remains separate from ordinary Analyze and must not silently appear as `AI probability`.

## 6. Locked validation

A calibration result can be reported as project evidence only after locked validation.

Required report sections:

- corpus composition by parent family;
- generator-held-out results where possible;
- hard-negative confusion table;
- processing-variant table;
- duration table;
- per-genre/style sensitivity;
- confidence intervals;
- known failure modes;
- comparison to calibration performance;
- whether the result supports only descriptive anomaly evidence or a stronger research classifier claim.

Any claim must match the strongest evidence actually obtained. Example wording:

```text
SUPPORTED: metric X differs in this corpus under condition Y.
NOT SUPPORTED: metric X proves AI origin in arbitrary music.
```

## 7. Repair validation

`TemporalStructureProfileV1` is useful to the repair pipeline only when a measured anomaly corresponds to an **audible, reviewed defect** or when it is used as a damage guard.

### 7.1 Entry gate

Before a temporal/spectral metric can drive a repair route:

- reviewed defect interval exists;
- at least two listeners or the current `GenerativeDefectProfileV1` review protocol confirms/marks ambiguity;
- metric evidence is localized or meaningfully linked to the reviewed defect;
- clean controls show acceptable false-positive behaviour;
- candidate repair is evaluated at matched loudness.

### 7.2 Before/after record

For each source/candidate pair store:

```text
source_asset_sha256
candidate_asset_sha256
parent_family_id
repair_route
repair_configuration_hash
alignment_method
applied_loudness_match_gain_db
source_temporal_profile
candidate_temporal_profile
delta_temporal_profile
artifact_reduction_rating
musical_damage_rating
transient_retention
mono/stereo_preservation
vocal_integrity
removed_signal_leakage
representative_region_results
verdict
```

### 7.3 Promotion criterion

A repair is **not** better merely because a temporal/spectral anomaly moves toward a human/control distribution.

Promotion requires:

```text
reviewed audible artifact improves
AND musical damage remains below gate
AND transient retention passes when applicable
AND vocal integrity passes when applicable
AND mono/stereo preservation passes
AND removed-signal leakage passes
AND all relevant representative-region classes pass
AND no hard technical failure occurs
```

If the metric improves but listeners do not hear an artifact improvement, classify the metric change as `NON_ACTIONABLE_EVIDENCE` for repair.

If a metric moves toward the calibrated range while useful musical content is removed, verdict is `REJECT` or `HUMAN_REVIEW` regardless of metric direction.

### 7.4 Candidate defect mappings

The following remain **candidate labels only** until calibration + listening evidence exists:

- `TRANSIENT_REPETITION`;
- `RHYTHMIC_MECHANICALITY`;
- `TEMPORAL_TIMBRE_ANOMALY`;
- `PERIODIC_SPECTRAL_ARTIFACT`.

Do not add them to a promoted defect taxonomy merely because the extractor outputs the corresponding measurements.

## 8. Deliverable artifacts

A complete research cycle should produce:

```text
source_registry.md
corpus_manifest.json/jsonl
processing_variant_manifest.json/jsonl
temporal_profiles.jsonl
distribution_summary.csv
distribution_report.md
calibration_record.json
locked_validation_report.md
repair_validation_pairs.jsonl
repair_validation_report.md
```

Private audio is not required in Git for the result to be reproducible if hashes, manifests, code/config identities and local corpus reconstruction instructions are retained.

## 9. Stage states

Use explicit stage states so future agents do not mistake plans for completed science:

```text
NOT_STARTED
PILOT
MEASURED
DISTRIBUTIONS_READY
CALIBRATED_RESEARCH
LOCKED_VALIDATED
REPAIR_VALIDATED
REJECTED
```

Current state at creation of this protocol:

```text
literature_registry: READY
extractor_prototype: READY
corpus_benchmark: NOT_STARTED
distributions: NOT_MEASURED
calibration: NOT_STARTED
locked_validation: NOT_STARTED
repair_validation: NOT_STARTED
```

## 10. Acceptance gate for #137 research completion

The research issue is not complete merely because `TemporalStructureProfileV1` exists.

Completion requires:

- [x] deterministic extractor prototype;
- [x] source/literature registry with scope limits;
- [x] corpus/distribution/calibration/repair-validation protocol;
- [ ] parent-family corpus manifest with mandatory hard negatives;
- [ ] raw/mastered/codec/stem-recombined variants measured;
- [ ] distribution report with overlap/effect-size/confound analysis;
- [ ] generator-held-out and processing-held-out validation;
- [ ] versioned calibration record or explicit evidence that calibration is not justified;
- [ ] locked-test report;
- [ ] before/after repair-validation report for any metric proposed as actionable defect evidence;
- [ ] no regression to ordinary MAEST/AST/CLaMP analysis;
- [ ] explicit MTD for each implementation/benchmark PR.

## Boundary

This protocol is for scientific characterization and repair-quality evidence. It is not an anti-detector-evasion workflow and does not optimize audio to hide provenance, remove watermarks, or minimize third-party detector scores.
