# Genre_test Roadmap

## Current release

**v0.4.0 — released**

Genre_test is currently a local music profiling and regression system:

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

The v0.4 release line remains the stable analysis baseline while v0.5 retrieval development proceeds independently.

## ACTIVE: v0.5 — CLaMP 3 semantic retrieval and catalog intelligence

Epic: **#26**  
Detailed roadmap: [`docs/CLAMP3_ROADMAP.md`](docs/CLAMP3_ROADMAP.md)  
Architecture: [`docs/CLAMP3_ARCHITECTURE.md`](docs/CLAMP3_ARCHITECTURE.md)

Selected direction: **CLaMP 3** for shared multilingual text↔music embeddings.

Product target:

```text
Анализ | Каталог | Поиск | Validation | Проверка
```

Core capabilities planned for v0.5:

- versioned retrieval/model-output architecture;
- isolated optional CLaMP 3 runtime until compatibility is proven;
- MERT-compatible audio preprocessing;
- track-level audio embeddings;
- Russian/multilingual text embeddings;
- persistent embedding cache;
- incremental exact-cosine catalog index;
- audio→audio similarity search;
- Russian free-text→music search;
- representative segment and custom segment retrieval;
- filters using existing Genre_test profile metadata;
- Catalog/Search GUI tabs;
- CLI search/index commands;
- retrieval relevance benchmark and regression gates;
- optional controlled zero-shot descriptor experiments;
- migration/indexing of the existing 10,436-track analyzed catalog;
- Windows bootstrap/portable integration;
- explicit third-party model provenance/license handling.

### v0.5 issue plan

P0 foundation:

- **#27** CLaMP 3 runtime compatibility spike / isolation decision
- **#28** retrieval schemas, backend protocol, embedding identity
- **#29** real CLaMP 3 + MERT backend adapter
- **#30** persistent embedding cache / incremental index
- **#41** model licensing and provenance gate

P1 product/search:

- **#31** audio-to-audio similarity search
- **#32** Russian multilingual free-text search
- **#33** segment embeddings / representative segment
- **#34** Catalog + Search GUI
- **#35** retrieval CLI / export
- **#36** relevance benchmark / regression

P2 graduation/release:

- **#37** controlled zero-shot descriptor experiments
- **#38** Windows bootstrap / portable retrieval runtime
- **#39** index the existing 10,436-track catalog
- **#40** documentation / migration / v0.5 release gate

### Critical runtime rule

CLaMP 3 does **not** replace MAEST, AST, BPM/key DSP, AudioProfile, history, or Validation. Retrieval is optional and must fail independently.

The official CLaMP 3 research environment differs materially from the released Genre_test core runtime. Initial work therefore assumes an isolated subprocess sidecar until #27 proves whether safer consolidation is possible.

### Critical license rule

CLaMP 3 is published as MIT, but its documented audio pipeline uses `m-a-p/MERT-v1-95M`, whose current model card declares `CC-BY-NC-4.0`. The MERT-backed retrieval backend is treated as optional/experimental and not claimed commercially unrestricted until #41 is resolved. Third-party model weights are not bundled in Git or portable packages.

### v0.5 exit criteria

- core v0.4 analysis/reference behavior remains green;
- CLaMP/MERT identity pinned and reproducible;
- retrieval absent => Analyze still works and reports Retrieval N/A;
- repeated same-input embedding is stable within documented tolerance;
- audio similarity and RU free-text search implemented;
- persistent catalog index survives restart and version changes safely;
- reviewed retrieval-quality corpus and metrics exist;
- current ~10k catalog can be indexed/reused incrementally;
- GUI and CLI both usable;
- Windows install/update tested;
- third-party license/provenance state explicit;
- final MTD before release.

## v0.4.x calibration work feeding v0.5

These remain valid but no longer block starting retrieval architecture:

### Performance and ambiguity

- decode audio once and share waveform between MAEST, DSP and AudioSet AST;
- persistent semantic inference cache by `track_id + model_revision`;
- optionally reuse ordinary analysis for byte-identical duplicates;
- benchmark AST overhead and VRAM use;
- calibrate semantic window count;
- calibrate MAEST/AST family fusion on reviewed tracks;
- expose fine-style ambiguity when Top-1/Top-2 margins are extremely small;
- explicit ambiguity/confidence for short input;
- independent BPM ground-truth fixtures.

### Benchmark and resolver calibration

- reviewed ground-truth table separate from run history;
- broad-family confusion/error analysis;
- selected fine-style confusion/error analysis;
- classical resolver/calibration;
- Validation severity calibration;
- mode-convergence fixtures such as xLaunge.

### Additional calibrated musical descriptors

Only add descriptors with a reproducible model or validated estimator:

- danceability;
- energy;
- acoustic/electronic balance;
- vocal presence probability;
- richer production descriptors.

CLaMP zero-shot descriptor experiments in #37 must follow the same rule: raw cosine similarity is not automatically a calibrated probability.

### Product mappings

- distributor taxonomy calibration;
- SUNO Style of Music ordering/length rules;
- configurable presentation mappings without changing stored evidence.

## Architecture rules

- obsolete TensorFlow-1/musicnn paths are not active product architecture;
- additional models must be reproducible and versioned;
- retrieval embeddings never silently overwrite analysis history;
- different embedding backend identities are never mixed in one search matrix without an explicit migration;
- third-party model licensing is tracked separately from Genre_test source licensing;
- new model failure must not silently degrade existing stable outputs.
