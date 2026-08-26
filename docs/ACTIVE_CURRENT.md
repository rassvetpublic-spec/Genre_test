# ACTIVE / CURRENT

Stable version: **0.4.0**  
Stable status: **released**  
Main release tag: `v0.4.0`  
Active development: **v0.5 CLaMP 3 semantic retrieval**  
Epic: **#26**  
Current first implementation issue: **#27**

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

## Active v0.5 direction: CLaMP 3

Selected backend family: **CLaMP 3**.

Purpose:

- audio→audio semantic similarity;
- Russian/multilingual free-text→music search;
- representative segment search;
- custom segment search;
- persistent local catalog embeddings;
- later controlled zero-shot descriptors.

Planned GUI surface:

```text
Анализ | Каталог | Поиск | Validation | Проверка
```

CLaMP 3 is an independent retrieval subsystem. It does not replace MAEST, AudioSet AST, tempo/key DSP, AudioProfile, history, or Validation.

Detailed docs:

- `docs/CLAMP3_ROADMAP.md`
- `docs/CLAMP3_ARCHITECTURE.md`
- `docs/CLAMP3_RUNTIME.md`
- `docs/THIRD_PARTY_MODELS.md`

## Retrieval runtime status

The CLaMP 3 runtime integration is currently in **compatibility-spike** phase (#27).

Captured upstream code snapshot for the spike:

```text
sanderwood/clamp3
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

Upstream research dependencies/runtime differ from stable Genre_test core. Current provisional architecture is an **optional isolated subprocess sidecar**, pending measurements.

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
- #34 GUI Catalog/Search
- #35 CLI/export
- #36 retrieval benchmark/regression

P2:

- #37 zero-shot descriptor experiments
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

No v0.5 feature PR is merged to `main` until explicit MTD. Runtime/model choices must be backed by measured compatibility, reproducibility, search-quality and licensing evidence.
