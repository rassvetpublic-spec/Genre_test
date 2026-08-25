# Genre_test Roadmap

## Product target

Genre_test должен быть не просто single-model genre classifier, а локальным музыкальным профайлером:

```text
Audio
  -> fine genre/style evidence
  -> independent semantic/tagging evidence
  -> BPM/key/audio features
  -> calibrated evidence fusion
  -> AudioProfile
  -> Normal / Technical / SUNO / Distributor / Similarity outputs
```

## 0.4.0 — Ensemble AudioProfile foundation

Status: implemented on `v0-4-0-audio-profile-foundation`, pending CI/local CUDA validation and merge.

- MAEST Discogs519 remains fine-style classifier.
- MIT AudioSet AST is independent semantic classifier.
- semantic genre, vocal, instrumentation, mood and production tags.
- deterministic evidence fusion with high-confidence MAEST protection.
- `AudioProfile` schema.
- result schema 4, backward-compatible loading.
- `normal`, `suno`, `distributor` presentation modes.
- semantic/profile data in JSON/history/summary CSV.
- semantic model revisions visible in diagnostics, not normal output.
- graceful MAEST-only fallback when semantic model is unavailable.
- existing raw-MAEST Validation baseline retained unchanged.

Release gate:

- Python 3.11/3.12 CI green.
- Ruff green.
- full unit suite green.
- Windows RTX CUDA smoke: MAEST + AST both on GPU.
- no raw-MAEST classification drift versus 0.3.6 when semantic layer is disabled.
- representative manual review of semantic vocal/instrument/mood tags.

## 0.4.1 — Performance and semantic calibration

Priority P0 after 0.4.0.

- decode audio once and share waveform between MAEST, DSP and semantic layer.
- benchmark AST overhead and VRAM consumption on RTX 5070 Ti.
- choose semantic window count from empirical accuracy/speed evidence.
- calibrate MAEST/AST family fusion weight on manually reviewed tracks.
- expose model agreement and semantic confidence without pretending scores are directly comparable across taxonomies.
- cache semantic inference by content `track_id + model_revision`.
- optionally skip re-analysis of byte-identical duplicate files in ordinary batch mode.

## 0.4.2 — Catalog and similarity

- XLSX export in addition to CSV/JSON.
- sortable catalog fields for genre/family/mood/vocal/instrumentation/BPM/key.
- track-to-track musical similarity.
- similarity should use embeddings/evidence vectors, not only final genre labels.
- nearest-neighbour list and compare-selected-tracks workflow.
- distinguish regression similarity from musical similarity.

## 0.4.3 — Additional musical descriptors

Only add descriptors with a reproducible model or validated estimator.

Targets:

- danceability;
- energy;
- acoustic/electronic balance;
- vocal presence probability;
- richer production descriptors.

Do not expose arbitrary 0..1 values unless the score source and calibration are defined.

## 0.4.4 — Product mappings

- calibrate distributor genre/subgenre mapping against actual target platform taxonomies.
- expand SUNO Style of Music generation with compact ordering rules and length limits.
- allow Normal/SUNO/Distributor outputs without altering raw stored evidence.
- user-configurable mapping profiles without changing model inference.

## 0.5 — Validated multi-model system

Exit criteria for 0.5:

- manually reviewed independent ground-truth set, not only version-to-version convergence;
- 20+ diverse external/reference tracks in addition to project catalog;
- confusion/error analysis for broad family and selected fine styles;
- calibrated ensemble thresholds;
- semantic tag precision review;
- documented failure modes;
- reproducible pinned models and schema migrations;
- semantic/profile regression checks in Validation Lab.

## Deliberately not used

Legacy `musicnn`/TensorFlow-1-era stack is not part of the default architecture because it would introduce a second obsolete runtime into the current Python 3.12/PyTorch application. A second model must be operationally independent in its learned taxonomy/evidence, not necessarily implemented in a different ML framework.

Essentia/Jamendo models remain candidates for later validation if they can be integrated reproducibly on the supported Windows/Python environment without destabilizing setup.
