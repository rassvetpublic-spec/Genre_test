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
Execution checklist: [`docs/CLAMP3_TODO.md`](docs/CLAMP3_TODO.md)  
Output scope: [`docs/CLAMP3_OUTPUT_SCOPE.md`](docs/CLAMP3_OUTPUT_SCOPE.md)  
Deferred ideas: [`docs/FAR_TODO.md`](docs/FAR_TODO.md)

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
- deterministic evidence-aware **Core Sound** summary (#43);
- conservative **Tempo / Structure Map** after segment foundation (#44);
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
- **#43** deterministic Core Sound description
- **#34** Catalog + Search GUI
- **#35** retrieval CLI / export
- **#36** relevance benchmark / regression

P2 graduation/release:

- **#37** controlled zero-shot descriptor experiments
- **#44** tempo map / structural change-point analysis
- **#38** Windows bootstrap / portable retrieval runtime
- **#39** index the existing 10,436-track catalog
- **#40** documentation / migration / v0.5 release gate

### Critical runtime rule

CLaMP 3 does **not** replace MAEST, AST, BPM/key DSP, AudioProfile, history, or Validation. Retrieval is optional and must fail independently.

The official CLaMP 3 research environment differs materially from the released Genre_test core runtime. Initial work therefore assumes an isolated subprocess sidecar until #27 proves whether safer consolidation is possible.

Target-machine inventory on 2026-08-26 confirms:

```text
Python 3.12 / 3.13 available
RTX 5070 Ti, 16 GB
compute capability 12.0
Torch 2.12.1+cu130
CUDA 13.0
native sm_120 compiled
```

Therefore the first real sidecar experiment uses a **modern Blackwell-capable Python 3.12 route**. The old upstream Python 3.10/CUDA 11.8 recipe remains reference evidence, not the desired production GPU path.

### Critical license rule

CLaMP 3 is published as MIT, but its documented audio pipeline uses `m-a-p/MERT-v1-95M`, whose current model card declares `CC-BY-NC-4.0`. The MERT-backed retrieval backend is treated as optional/experimental and not claimed commercially unrestricted until #41 is resolved. Third-party model weights are not bundled in Git or portable packages.

### v0.5 output truth rule

New richer text must preserve the distinction:

```text
MEASURED / MODEL EVIDENCE
    -> RESOLVED ANALYSIS
    -> DETERMINISTIC DESCRIPTION
    -> OPTIONAL CREATIVE RECOMMENDATIONS (future)
```

For v0.5:

- `Core Sound` is a deterministic summary of existing/versioned evidence, not new evidence;
- CLaMP zero-shot scores remain raw similarities until calibrated;
- `Production era` means perceived sonic era, not release year;
- Tempo/Structure Map may identify conservative change points but does not automatically claim Verse/Chorus/Drop labels;
- no specific plug-in/processor may be inferred as fact from rendered audio.

### v0.5 exit criteria

- core v0.4 analysis/reference behavior remains green;
- CLaMP/MERT identity pinned and reproducible;
- retrieval absent => Analyze still works and reports Retrieval N/A;
- repeated same-input embedding is stable within documented tolerance;
- audio similarity and RU free-text search implemented;
- persistent catalog index survives restart and version changes safely;
- reviewed retrieval-quality corpus and metrics exist;
- current ~10k catalog can be indexed/reused incrementally;
- deterministic Core Sound output is evidence-traceable;
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

Only add descriptors with a reproducible model or validated estimator.

Active experimental candidate set in #37:

- mood/emotion;
- character;
- movement/groove;
- energy bands;
- small vocal presence/style vocabulary;
- production era / sonic decade;
- use-case descriptors.

CLaMP zero-shot raw cosine similarity is not automatically a calibrated probability.

### Product mappings

- distributor taxonomy calibration;
- SUNO Style of Music ordering/length rules;
- configurable presentation mappings without changing stored evidence.

## FAR TODO

Useful but non-blocking ideas are kept in [`docs/FAR_TODO.md`](docs/FAR_TODO.md) instead of inflating v0.5:

- rich vocal register/timbre/diction/spatial profile;
- detailed kick/snare/hat/808 decomposition;
- full production/mastering profile;
- plug-in/processor inference;
- creative arrangement advice;
- semantic Verse/Chorus/Bridge/Drop naming;
- detailed motif/transcription analysis;
- AI-origin detection;
- million-track ANN/search infrastructure;
- cloud/external integrations.

Items move out of FAR TODO only after evidence source, license, schema, reviewed fixtures, precision/repeatability and failure semantics are defined.

## Architecture rules

- obsolete TensorFlow-1/musicnn paths are not active product architecture;
- additional models must be reproducible and versioned;
- retrieval embeddings never silently overwrite analysis history;
- different embedding backend identities are never mixed in one search matrix without an explicit migration;
- third-party model licensing is tracked separately from Genre_test source licensing;
- new model failure must not silently degrade existing stable outputs;
- attractive natural-language output is never allowed to outrun the evidence that supports it.
