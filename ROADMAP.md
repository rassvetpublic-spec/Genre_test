# Genre_test Roadmap

## Current stable line

**v0.4.0 — released.**

The active architecture is:

```text
Audio
  -> MAEST detailed genre/style evidence
  -> AudioSet AST semantic evidence
  -> BPM/key/source metadata
  -> calibrated evidence fusion
  -> AudioProfile
  -> Normal / SUNO / Distributor
  -> History / Validation / build comparison
```

Legacy portable 0.3.x is retired. Older history snapshots remain readable only for regression/data compatibility.

## 0.4.1 — ambiguity and regression quality

Priority: P0/P1.

- margin-aware Top-1 / Top-2 ambiguity reporting;
- short-input ambiguity policy;
- independent ground-truth BPM set for half/double/3:2 cases;
- xLaunge mode-convergence investigation;
- expand registered regression corpus;
- large-corpus repeatability and build-to-build reports;
- stronger genre/family/secondary-influence consistency tests.

## 0.4.2 — performance and cache

- decode audio once and share waveform between MAEST, DSP and AudioSet AST;
- persistent semantic cache by `track_id + model_revision`;
- skip byte-identical duplicate inference where safe;
- benchmark AST/MAEST VRAM and throughput on RTX 5070 Ti;
- tune semantic window count from measured accuracy/speed evidence;
- improve warm-start and multi-track throughput telemetry.

## 0.4.3 — catalog and similarity

- XLSX export in addition to CSV/JSON;
- sortable catalog for genre/family/mood/vocal/instrumentation/BPM/key;
- track-to-track musical similarity;
- embeddings/evidence-vector similarity instead of label-only similarity;
- nearest-neighbour and compare-selected-tracks workflow;
- separate musical similarity from regression similarity.

## 0.4.4 — additional musical descriptors

Only expose descriptors with a reproducible model or validated estimator.

Candidates:

- danceability;
- energy;
- acoustic/electronic balance;
- vocal presence probability;
- richer production descriptors;
- instrumentation confidence.

Do not expose arbitrary 0..1 values unless the score source and calibration are defined.

## 0.4.5 — product mappings

- calibrate distributor genre/subgenre mapping against target platform taxonomies;
- improve SUNO Style of Music ordering, ambiguity handling and compactness;
- user-configurable presentation mappings without changing stored evidence;
- preserve deterministic Normal/SUNO/Distributor formatting.

## 0.5 — validated multi-model system

Exit criteria:

- manually reviewed ground-truth set, not only version-to-version convergence;
- diverse external/reference corpus in addition to project catalog;
- confusion/error analysis for broad family and selected fine styles;
- calibrated ensemble thresholds;
- semantic tag precision review;
- documented failure modes;
- reproducible pinned models and schema migrations;
- semantic/profile regression inside Validation Lab;
- stable large-corpus automation suitable for release gating.

## Architecture rule

A second model must add genuinely independent learned evidence. It does not need to use a different ML framework merely for diversity.

Legacy TensorFlow-1-era stacks are not part of the supported runtime. New model additions must work reproducibly in the supported Python/PyTorch environment without destabilizing Windows setup.
