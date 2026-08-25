# Genre_test Roadmap

## Current release

**v0.4.0 — released**

Genre_test is now a local music profiling and regression system:

```text
Audio
  -> MAEST Discogs519 fine-style evidence
  -> AudioSet AST semantic evidence
  -> BPM / key / native source metadata
  -> calibrated evidence fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor outputs
  -> history / Validation / build comparison
```

Implemented in v0.4.0:

- Python 3.11 / 3.12 / 3.13 x64 support
- PyTorch 2.12.1
- CUDA 13.0 / cu130 NVIDIA route
- Blackwell native architecture gate (`sm_120` verified on RTX 5070 Ti)
- CPU-only fallback with `CUDA: N/A | GPU: N/A`
- one-click working-copy and packaged bootstrap
- dark theme by default with live theme switching
- live mode / view / full-path / device controls
- Safe Stop
- Expert MAEST windows + guarded Top-K
- build-aware history identity
- separate Анализ / Validation / Проверка tabs
- saved-build comparison preflight and repeatability mode
- explicit DRIFT terminology
- Genre/Family reconciliation
- weak AST absolute-confidence protection
- tempo-v2 half/double + short 3:2 handling
- native source metadata independent from the 16 kHz model stream
- GitHub Release + repository `releases/` package publication

## v0.4.1 — performance and ambiguity calibration

Priority P1.

- decode audio once and share waveform between MAEST, DSP and AudioSet AST
- persistent semantic inference cache by `track_id + model_revision`
- optionally reuse ordinary analysis for byte-identical duplicates
- benchmark AST overhead and VRAM use on RTX 5070 Ti
- calibrate semantic window count
- calibrate MAEST/AST family fusion weight on manually reviewed tracks
- expose fine-style ambiguity when Top-1 / Top-2 margins are extremely small
- add explicit ambiguity/confidence output for short input
- establish independent BPM ground-truth fixtures instead of treating stable output as truth

## v0.4.2 — benchmark and resolver calibration

- run a large mixed catalog after v0.4.0 release
- maintain a reviewed ground-truth table separate from run history
- include external/reference tracks in addition to project catalog
- broad-family confusion/error analysis
- selected fine-style confusion/error analysis
- classical period/style resolver
- calibrate Validation severity thresholds against observed false alarms
- track mode-convergence fixtures such as xLaunge

## v0.4.3 — catalog and similarity

- XLSX export in addition to CSV/JSON
- sortable catalog fields for genre/family/mood/vocal/instrumentation/BPM/key
- track-to-track musical similarity using evidence vectors/embeddings, not only final labels
- nearest-neighbour list
- selected-track comparison workflow

## v0.4.4 — additional calibrated musical descriptors

Only add descriptors with a reproducible model or validated estimator:

- danceability
- energy
- acoustic/electronic balance
- vocal presence probability
- richer production descriptors

Do not expose arbitrary 0..1 values without a defined score source and calibration method.

## v0.4.5 — product mappings

- calibrate distributor genre/subgenre mapping against target platform taxonomies
- refine compact SUNO Style of Music ordering/length rules
- configurable presentation mappings without changing stored model evidence

## v0.5 — validated multi-model system

Exit criteria:

- independently reviewed ground-truth corpus
- 20+ diverse external/reference tracks plus project catalog
- documented broad/fine-style error analysis
- calibrated ensemble thresholds
- semantic tag precision review
- documented failure modes
- pinned reproducible models and schema migrations
- semantic/profile regression checks inside Validation Lab

## Architecture rule

Obsolete TensorFlow-1-era/musicnn runtime paths are not part of the active product. Additional models must integrate reproducibly with the supported Windows/Python runtime and provide genuinely independent evidence.
