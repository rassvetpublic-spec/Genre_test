# CLaMP 3 / Semantic Retrieval Roadmap

Status: **ACTIVE DEVELOPMENT**  
Parent epic: **#26**  
Release target: **Genre_test v0.5**  
Selected retrieval family: **CLaMP 3**

Supporting scope docs:

- [`CLAMP3_OUTPUT_SCOPE.md`](CLAMP3_OUTPUT_SCOPE.md)
- [`FAR_TODO.md`](FAR_TODO.md)
- [`CLAMP3_WINDOWS_SPIKE_2026-08-26.md`](CLAMP3_WINDOWS_SPIKE_2026-08-26.md)

## 1. Product objective

Genre_test v0.5 expands the released v0.4 profiler/regression lab into a local semantic music catalog:

```text
Audio
 ├─ existing analysis
 │   ├─ MAEST Discogs519
 │   ├─ AudioSet AST
 │   ├─ DSP / BPM / key / source metadata
 │   └─ AudioProfile + history + Validation
 │
 └─ retrieval analysis
     ├─ MERT-compatible audio frontend
     ├─ CLaMP 3 audio embedding
     ├─ track / segment embedding cache
     └─ exact cosine catalog index

Russian / multilingual text
 └─ CLaMP 3 text embedding
     └─ same shared embedding space
         └─ text -> music search
```

CLaMP 3 is an **independent retrieval subsystem**. It does not replace MAEST genre classification, AST semantic evidence, tempo/key DSP, `AudioProfile`, history, or Validation.

v0.5 also adds two evidence-aware analysis outputs that directly benefit retrieval/product UX:

- **#43 Core Sound** — deterministic natural-language summary from versioned evidence;
- **#44 Tempo / Structure Map** — conservative temporal tempo/change-point analysis after segment foundation.

## 2. Why CLaMP 3

The upstream CLaMP 3 project aligns audio, multilingual text and other music modalities in a shared contrastive space. Its public design uses multilingual XLM-R text representation and is suitable for testing Russian text→music retrieval.

Primary intended Genre_test use cases:

1. audio -> audio similarity;
2. Russian text -> audio semantic retrieval;
3. representative segment -> catalog search;
4. custom segment -> catalog search;
5. controlled zero-shot descriptor experiments;
6. deterministic explanation of search/profile results through structured evidence.

## 3. Upstream facts captured for the spike

Candidate upstream code snapshot:

```text
repository: https://github.com/sanderwood/clamp3
commit:     9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

The upstream requirements at that snapshot include pinned older package versions such as `transformers==4.40.0`, `accelerate==0.34.0`, `numpy==1.26.4`, `nnAudio==0.3.3` and related research dependencies.

The upstream quick start documents an environment around:

```text
Python 3.10.16
PyTorch + CUDA 11.8
```

Genre_test core remains:

```text
Python 3.11 / 3.12 / 3.13
PyTorch 2.12.1
CUDA 13.0 / cu130
Windows-first
```

Target Windows inventory captured on 2026-08-26 confirms:

```text
Python 3.12 + 3.13 installed
RTX 5070 Ti / 16303 MiB
Driver 610.88
Compute capability 12.0
Core Torch 2.12.1+cu130
CUDA 13.0
native sm_120 compiled
```

Therefore the first real GPU experiment is an **isolated modern Python 3.12 / Blackwell-capable sidecar**. The old upstream Python 3.10/CUDA 11.8 environment remains a behavioral/reference baseline, not the desired production GPU route.

Upstream audio preprocessing uses MERT-style features with 24 kHz mono audio and 5-second sliding windows before CLaMP processing. The exact preprocessing behavior must be pinned as part of embedding identity.

## 4. License gate

CLaMP 3 itself is published as MIT. Its documented audio path uses `m-a-p/MERT-v1-95M`; the current MERT model card declares `CC-BY-NC-4.0`.

Until #41 is resolved:

- the MERT-backed CLaMP integration is treated as optional/experimental;
- Genre_test does not redistribute MERT weights;
- no claim is made that the MERT-backed stack is commercially unrestricted;
- model provenance and licenses must be visible in documentation and diagnostics.

This is a release-policy concern, not a reason to stop local technical prototyping.

## 5. Milestone map

### M0 — architecture, compatibility, provenance

Issues: **#27, #28, #41**

Deliverables:

- Windows compatibility matrix;
- selected runtime isolation model;
- CLaMP/MERT/model provenance pins;
- backend health contract;
- versioned embedding identity;
- retrieval storage schema;
- no regression to v0.4 analysis.

Exit gate:

- ordinary Analyze works with retrieval completely absent;
- CI needs no CLaMP/MERT downloads;
- retrieval failure is isolated and observable.

### M1 — real embeddings and cache

Issues: **#29, #30**

Deliverables:

- real audio embedding;
- real Russian text embedding;
- L2-normalized vector contract;
- persistent cache;
- stale detection;
- incremental index;
- index stats/rebuild tools.

Exit gate:

- same input/backend is repeatable within documented cosine tolerance;
- second indexing pass recomputes nothing unchanged;
- backend identity change makes previous vectors stale instead of silently mixing them.

### M2 — retrieval and time-aware representation

Issues: **#31, #32, #33**

Deliverables:

- audio -> audio Top-K search;
- Russian text -> audio Top-K search;
- structured catalog filters;
- representative segment;
- custom segment search;
- deterministic ranking.

Baseline ranking:

```text
L2-normalized vectors
        -> cosine similarity
        -> stable descending sort
        -> deterministic tie break
```

For the current ~10k catalog, exact vector search is preferred before adding FAISS/HNSW complexity.

### M3 — evidence-aware output and product surface

Issues: **#43, #34, #35**

`#43 Core Sound`:

- deterministic summary;
- no LLM required in baseline;
- every phrase traceable to structured evidence;
- compact SUNO-facing ordering may be derived separately;
- weak evidence results in a shorter description, not invented detail.

Target GUI:

```text
Анализ | Каталог | Поиск | Validation | Проверка
```

Catalog tab:

- source roots;
- indexed/stale/missing/failed counters;
- backend identity;
- incremental update;
- stale-only rebuild;
- full rebuild;
- Safe Stop;
- progress/ETA/cache-hit statistics.

Search tab:

- Text / Audio / Catalog Track query;
- Full / Representative / Custom segment scope;
- Top-K;
- family/genre/BPM/key/confidence/vocal/folder filters;
- similarity-ranked results;
- JSON/CSV export.

CLI parity is mandatory.

### M4 — quality and regression

Issue: **#36**

Build manually reviewed retrieval relevance data, separate from analysis history.

Metrics:

- Precision@K;
- Recall@K;
- MRR;
- nDCG@K;
- RU/EN paired-query overlap;
- self-match sanity;
- embedding repeatability;
- search latency P50/P95;
- indexing throughput/cache-hit rate.

No retrieval-quality claim is allowed solely because the model returns visually plausible neighbours.

### M5 — optional descriptors and temporal structure

Issues: **#37, #44**

Controlled CLaMP descriptor experiments:

- mood/emotion;
- character;
- movement/groove;
- energy bands;
- small vocal presence/style vocabulary;
- production era / sonic decade;
- sync/use-case descriptors.

CLaMP cosine similarities are not probabilities. User-facing scores require calibration and reviewed precision.

CLaMP genre prompts do **not** enter the MAEST/AST production resolver in this milestone.

`#44 Tempo / Structure Map` adds conservative temporal outputs:

- per-segment tempo and ambiguity;
- sustained tempo/rhythm change points;
- stable-tempo false-positive protection;
- backward compatibility with global tempo-v2.

It does **not** promise Verse/Chorus/Drop labels or specific transition-effect identification.

### M6 — Windows packaging and existing-catalog migration

Issues: **#38, #39**

Deliverables:

- optional retrieval install;
- isolated model/runtime lifecycle;
- resumable indexing;
- existing v0.4 history reuse;
- CLaMP-only reprocessing of the current catalog;
- no unnecessary MAEST/AST re-analysis;
- full index coverage/report.

Current first real corpus:

```text
10,439 discovered files
10,436 successful v0.4 Auto analyses
10,383 AST semantic OK
~775 h of audio
```

### M7 — documentation and v0.5 release

Issue: **#40**

Release gates:

- v0.4 reference behavior remains green;
- retrieval unit/integration tests green;
- Windows GPU smoke green;
- optional/unavailable backend behavior green;
- real catalog indexing report archived;
- RU text retrieval manually reviewed;
- audio similarity manually reviewed;
- retrieval benchmark recorded;
- Core Sound evidence tracing reviewed;
- license/provenance state explicit;
- portable install/update tested;
- final MTD/branch cleanup.

## 6. Dependency graph

```text
#26 EPIC
 |
 +-- #27 runtime spike --------------------+
 |                                         |
 +-- #41 licensing/provenance              |
 |                                         v
 +-- #28 schemas/protocol -------------> #29 real backend
                                         |
                                         v
                                      #30 cache/index
                                      /   |   \
                                     /    |    \
                                  #31    #32    #33
                                   |      |      |
                                   +------+------+
                                          |
                                  +-------+--------+
                                  |                |
                                #43             #44
                           Core Sound       Tempo/Structure
                                  |
                          +-------+-------+
                          |               |
                        #34 GUI         #35 CLI
                          |               |
                          +-------+-------+
                                  |
                                #36 benchmark
                                  |
                         +--------+--------+
                         |                 |
                       #37               #38
                descriptors exp.      packaging
                                           |
                                         #39
                                    full catalog
                                           |
                                         #40
                                      v0.5 gate
```

## 7. Data architecture target

Retrieval data is deliberately separate from analysis run history.

Proposed state layout:

```text
.genre_test/
  history.sqlite3
  logs/
  retrieval/
    retrieval.sqlite3
    vectors/
    index/
    cache/
    runtime/
    models/
```

Proposed retrieval tables:

```text
embedding_models
track_embeddings
segment_embeddings
search_index_meta
search_runs
```

Required identity dimensions include:

```text
backend name/version
CLaMP code revision
CLaMP weight identity/checksum
MERT model id/revision
preprocessing version
embedding dimension
normalization rule
track_id
segment start/end
```

Future `Core Sound` and temporal outputs get their own rule/schema version and do not alter raw embedding identity.

## 8. Search filters reuse existing analysis

CLaMP should answer semantic similarity. Existing Genre_test data remains useful for deterministic filtering:

```text
CLaMP similarity
  + AudioProfile family/genre
  + BPM
  + key
  + confidence
  + mood/vocal/instruments/production
  + folder/path
  = product search result
```

Do not force these structured fields into the embedding itself.

## 9. Performance strategy

For 10,500 vectors at 768 float32 dimensions:

```text
~32 MB raw vector matrix
```

Exact NumPy cosine ranking should be the first implementation. ANN is only introduced after measured need.

Segment embeddings can multiply storage/inference substantially; #33 must benchmark a subset before indexing every segment of ~775 hours.

## 10. CI strategy

CI must stay lightweight:

- fake deterministic backend fixture;
- tiny synthetic vectors;
- schema/serialization tests;
- search/ranking/filter tests;
- deterministic Core Sound template tests;
- tempo/structure synthetic fixtures when #44 starts;
- subprocess protocol tests;
- no multi-GB model download;
- no GPU requirement.

Real CLaMP/MERT inference belongs to local/release hardware gates with archived evidence.

## 11. Scope boundary / FAR TODO

Rich ideas that are not required for v0.5 are preserved in [`FAR_TODO.md`](FAR_TODO.md), including:

- detailed vocal register/timbre/diction/spatial profile;
- event-level drum/808 decomposition;
- complete production/mastering profile;
- plug-in/processor inference;
- creative arrangement advice;
- semantic Verse/Chorus/Bridge/Drop naming;
- detailed motif/transcription analysis;
- AI-origin detection;
- million-track ANN infrastructure;
- cloud/external integrations.

An item moves into active development only after its evidence source, license, versioned schema, reviewed fixtures, precision/repeatability and failure semantics are defined.

## 12. Definition of done

v0.5 is done only when:

1. CLaMP/MERT identity is reproducible and documented;
2. runtime isolation is stable on Windows;
3. audio embeddings are cached/versioned;
4. Russian free-text retrieval works;
5. audio similarity works;
6. representative/custom segment search works;
7. catalog/index survives restart and upgrades safely;
8. deterministic Core Sound output is evidence-traceable;
9. reviewed retrieval benchmark exists;
10. GUI + CLI are both usable;
11. third-party license state is explicit;
12. v0.4 analysis and Validation remain intact;
13. release passes MTD.
