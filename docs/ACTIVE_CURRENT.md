# ACTIVE / CURRENT

Stable version: **0.4.0**  
Stable status: **released**  
Main release tag: `v0.4.0`  
Active development version: **0.5.0.dev0**  
Active development scope: **v0.5 CLaMP 3 semantic retrieval**  
Epic: **#26**  
Current first implementation issue: **#27**

Long-term product epic: **#49 SUPERCOMBINE**  
Long-term execution TODO: `docs/SUPERCOMBINE_TODO.md`  
Geekatplay reuse audit: `docs/GEEKATPLAY_ORG_AUDIT.md`

## Product north star

Genre_test is no longer planned as only a genre analyzer. The post-v0.5 direction is a local-first finishing workstation for generative songs:

```text
Generated mix / stems
  -> Analyze / Catalog / Search
  -> Technical QC + markers
  -> Repair artifacts
  -> Vocal/stem post-processing
  -> Mix/master orchestration
  -> Synchronized A/B/X review
  -> Metadata/tag audit
  -> Delivery / studio-ready master
```

The target is removal of audible defects and weak/raw generative production characteristics while keeping immutable sources, evidence provenance and reproducible processing manifests. **AI-detector evasion / provenance concealment is not a product objective.**

Planned long-term phases:

- v0.6 Repair & Stem Lab — #50, #51, #52; Apollo compatibility/restoration robustness is tracked in #63 under #50;
- v0.7 Studio Finish / mastering orchestration — including #54 comparison lab;
- v0.8 Metadata/Catalog/Delivery — #53, #56;
- v0.9 ComfyUI/runtime orchestration — #46, #55;
- v1.0 integrated SUPERCOMBINE.

## Stable v0.4 implementation

Genre_test 0.4.0 remains a local Windows-first music profiling and regression system built around:

```text
Audio
  -> MAEST Discogs519 fine-style evidence
  -> AudioSet AST semantic evidence
  -> BPM / key / source metadata
  -> deterministic profile fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor views
  -> history / Validation / build comparison
```

No v0.5 retrieval work may silently change these outputs without separate review and evidence.

## Runtime baseline

Stable core:

- Python 3.11 / 3.12 / 3.13 x64
- PyTorch 2.12.1
- NVIDIA: CUDA 13.0 / cu130
- Blackwell requires native active architecture; RTX 5070 Ti `sm_120` verified
- CPU-only supported; GUI reports `CUDA: N/A | GPU: N/A`
- NVIDIA present but unusable CUDA is a runtime failure, not CPU fallback
- FFmpeg bootstrap and diagnostics included
- public pinned Hugging Face analysis models work anonymously; token optional

### Actual target workstation inventory — 2026-08-26

```text
Windows 11 Pro Insider Preview 10.0.26220
Python 3.12 + 3.13 installed
Python 3.10/3.11 not registered
Core Python 3.12.10
RTX 5070 Ti / 16303 MiB / driver 610.88
compute capability 12.0
Torch 2.12.1+cu130
CUDA 13.0
native sm_120 present
FFmpeg available
```

Evidence: `docs/CLAMP3_WINDOWS_SPIKE_2026-08-26.md`.

The current CLaMP spike therefore prioritizes a **modern isolated Python 3.12 Blackwell-capable sidecar**. The older upstream Python 3.10/CUDA 11.8 environment is reference evidence only and is not the target RTX 5070 Ti production route.

## Active v0.5 direction: CLaMP 3

Selected backend family: **CLaMP 3**.

Purpose:

- audio→audio semantic similarity;
- Russian/multilingual free-text→music search;
- representative segment search;
- custom segment search;
- persistent local catalog embeddings;
- deterministic Core Sound summary;
- later controlled zero-shot descriptors;
- conservative tempo/structure timeline after segment foundation.

Planned GUI surface:

```text
Анализ | Каталог | Поиск | Validation | Проверка
```

CLaMP 3 is an independent retrieval subsystem. It does not replace MAEST, AudioSet AST, tempo/key DSP, AudioProfile, history, or Validation.

Detailed docs:

- `docs/CLAMP3_ROADMAP.md`
- `docs/CLAMP3_ARCHITECTURE.md`
- `docs/CLAMP3_RUNTIME.md`
- `docs/CLAMP3_TODO.md`
- `docs/CLAMP3_OUTPUT_SCOPE.md`
- `docs/FAR_TODO.md`
- `docs/THIRD_PARTY_MODELS.md`
- `docs/SUPERCOMBINE_TODO.md`
- `docs/GEEKATPLAY_ORG_AUDIT.md`

## Retrieval runtime status

The CLaMP 3 runtime integration is currently in **compatibility-spike** phase (#27).

Captured upstream code snapshot for the spike:

```text
sanderwood/clamp3
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

Current provisional architecture is an **optional isolated subprocess sidecar**, pending real MERT/CLaMP inference measurements.

Expected optional health behavior:

```text
Retrieval: N/A   backend not installed/enabled
Retrieval: OK    backend/model/index ready
Retrieval: WARN  usable degraded/stale state
Retrieval: FAIL  installed/configured but not operational
```

Retrieval N/A/FAIL must not make ordinary Analyze unusable.

## Third-party model gate

CLaMP 3 is published with MIT metadata, but the documented CLaMP audio path relies on `m-a-p/MERT-v1-95M`, whose current public model card declares `CC-BY-NC-4.0`.

Until #41 is resolved:

- retrieval development is optional/experimental;
- no MERT weights are committed or bundled in portable ZIPs;
- the MERT-backed stack is not described as commercially unrestricted;
- exact model revisions/checksums/licenses must be shown in provenance diagnostics before release indexing.

## v0.5 output scope

Promoted into active v0.5 work:

- **#43 Core Sound** — deterministic evidence-aware human description;
- **#44 Tempo / Structure Map** — conservative segment tempo/change-point output;
- **#37 controlled descriptors** — mood/character/movement/energy plus small vocal and production-era experiments, but only after calibration;
- **#45 TechnicalProfile** — selective objective Music Suite metrics/markers;
- **#48 Resource Monitor** — live CPU/RAM/GPU/VRAM telemetry.

Explicitly deferred to `docs/FAR_TODO.md`:

- rich vocal register/timbre/diction/spatial profile;
- detailed kick/snare/hat/808 decomposition;
- perceptual production/mastering labels beyond validated TechnicalProfile metrics;
- plug-in/processor inference;
- creative arrangement advice;
- semantic Verse/Chorus/Bridge/Drop naming;
- detailed motif/transcription analysis;
- AI-origin detection;
- million-track ANN infrastructure;
- cloud/external integrations.

Truth hierarchy:

```text
MEASURED / MODEL EVIDENCE
  -> RESOLVED ANALYSIS
  -> DETERMINISTIC DESCRIPTION
  -> OPTIONAL CREATIVE RECOMMENDATIONS (future)
```

Descriptions must never outrun their evidence.

## v0.5 issue map

P0:

- #27 runtime compatibility/isolation
- #28 retrieval schemas/protocol
- #29 real CLaMP+MERT backend
- #30 persistent embedding cache/index
- #41 model license/provenance

P1:

- #31 audio similarity
- #32 Russian free-text search
- #33 segment/representative search
- #43 deterministic Core Sound
- #34 GUI Catalog/Search
- #35 CLI/export
- #36 retrieval benchmark/regression
- #45 TechnicalProfile foundation
- #48 Resource Monitor

P2:

- #37 zero-shot descriptor experiments
- #44 tempo/structure map
- #38 Windows bootstrap/portable
- #39 index current 10,436-track catalog
- #40 docs/migration/release gate

## Current large-catalog evidence

The first real retrieval corpus is available from the completed v0.4 collection run:

```text
10,439 discovered files
10,436 successful Auto analyses
10,383 semantic OK
~775 h audio
```

This existing analysis/history should be reused as catalog metadata. CLaMP indexing should not unnecessarily rerun MAEST/AST.

## Geekatplay integration status

Forks exist:

```text
rassvetpublic-spec/music-suite
rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

Selected ideas beyond the existing fork work are documented in `docs/GEEKATPLAY_ORG_AUDIT.md`.

Especially useful directions:

- Music Suite metadata/markers/mastering orchestration patterns;
- Song Geometry Mapper time/feature/edge concepts;
- Sonic Holodeck heavy-model cache concept;
- ABCvers synchronized comparison UX;
- Asset Vault integrity/provenance/lineage and safe-operation patterns;
- Whisper-related transcription architectures as research references only.

## Stable v0.4 product behavior

- default output view: `all`
- optional full source path
- live Device / mode / view / path switching between tracks
- Safe Stop for Analysis and Validation
- dark theme by default with live Dark / Light switching
- Expert mode exposes MAEST windows and Top-K
- CPU-only UI does not offer CUDA
- History and log paths clickable

## AudioProfile

- MAEST remains the fine-style classifier
- pinned MIT AudioSet AST provides independent semantic evidence
- genre/family reconciliation prevents contradictory published profiles
- weak AST family evidence retains absolute-confidence protection
- semantic failure in auto mode falls back to MAEST-only

## Tempo and metadata

- tempo-v2 handles half/double and short-loop 3:2 ambiguity
- source sample rate / bit depth / channels / bitrate come from original source
- independent BPM ground-truth remains future calibration work
- #44 must preserve backward compatibility with global tempo-v2 until benchmark evidence justifies any replacement

## Validation / history

Default working-copy paths:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\results\
```

Retrieval state will be separate under `.genre_test/retrieval/` so indexing changes cannot destroy analysis history.

Current history identity includes analyzer version, Git commit, schema, model revision, analysis mode, run id and timestamp.

Validation keeps explicit `DRIFT: STABLE/MINOR/SIGNIFICANT/CRITICAL` terminology.

## Release packaging

Stable package:

```text
releases\Genre_test_0.4.0_portable.zip
releases\SHA256SUMS.txt
```

v0.5 retrieval runtime/model weights are **not** yet part of the stable package.

## Current development rule

`Genre_test_START.cmd` is the single supported user entry point for dependency installation, environment checks, optional retrieval runtime management and application startup. Files under `scripts/` are internal implementation details invoked by the launcher.

No v0.5 feature PR is merged to `main` until explicit MTD. Runtime/model choices must be backed by measured compatibility, reproducibility, search-quality and licensing evidence.

The same merge rule applies to SUPERCOMBINE work: no future repair/master/tag/runtime feature is merged without explicit MTD.
