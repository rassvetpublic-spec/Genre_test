# AI Origin & Provenance Lab — Roadmap

Parent epic: **#80**  
Architecture: [`AI_ORIGIN_PROVENANCE_LAB.md`](AI_ORIGIN_PROVENANCE_LAB.md)  
Status: planned / implementation not started.

## North star

Build a local, calibrated, evidence-traceable origin detector that can distinguish likely human vs AI-generated music, identify supported generator families when justified, remain useful on unseen generators, and keep verified-human false positives tightly controlled.

Primary target runtime: RTX 5070 Ti 16 GB / Blackwell `sm_120` using the existing PyTorch 2.12.1+cu130 stack and proven MERT sidecar.

## P0 — Truth, benchmark and physical baseline

### #81 OriginProfileV1 + benchmark protocol

Deliver first:
- schema and uncertainty semantics;
- corpus manifest;
- LOGO split implementation;
- Recall@fixed-FPR metrics;
- duplicate/remaster/leakage guards;
- Verified Human provenance/strata contract.

Exit gate: benchmark plumbing is deterministic and cannot hide the worst generator or worst human stratum.

### #82 Native forensic path + Fourier fakeprint

Deliver:
- one-decode/multiple-view foundation where practical;
- native/high-rate forensic view;
- CPU Fourier/decoder fakeprint extractor;
- lightweight baseline classifier;
- interpretable evidence export.

Exit gate: establishes the first locked origin-detection baseline before heavy ML streams are introduced.

## P1 — Robust local forensic + long context

### #83 CQT forensic CNN

Mandatory robustness matrix:
- variable MP3/AAC/Opus bitrates;
- resampling;
- EQ/compression/limiting/loudness normalization;
- phase rotation and plausible channel-phase perturbations;
- controlled noise.

Exit gate: adds measurable value at fixed verified-human FPR and does not become a codec/bitrate classifier.

### #84 Shared MERT + overlapping long context

Accepted default segmentation candidate:

```text
window = 5.0 s
stride = 2.5 s
```

Mandatory ablation: compare against 5.0/5.0 non-overlap.

Deliver:
- versioned MERT segment cache;
- reuse by origin/retrieval when identities match;
- compact sequence detector;
- boundary-localized timestamp evidence;
- no overlap leakage across dataset partitions.

Exit gate: measurable worst-fold improvement at controlled human FPR within RTX 5070 Ti resource limits.

## P2 — Unknown generators, attribution and calibrated fusion

### #85 Verified Human novelty / OOD

Human reference data must explicitly cover:
- modern native/lossless masters;
- remasters;
- old digitizations/legacy masters;
- lossy human sources;
- live/acoustic;
- electronic/heavily processed;
- genre-balanced, artist-disjoint subsets.

Benchmark Mahalanobis/kNN/simple one-class baselines before compact flows.

Exit gate: improves unseen-generator recall or uncertainty while keeping per-stratum human FPR controlled.

### #86 Generator-family attribution

Hierarchical output:

```text
AI -> SUNO / UDIO / MUSICGEN / STABLE_AUDIO / AUDIOLDM / RIFFUSION / OTHER_AI
```

`UNKNOWN` and `OTHER_AI` are required rejection states.

Exit gate: source attribution does not force weak known labels onto unsupported generators.

### #87 Multi-stream fusion + conformal uncertainty

Fuse only streams that earned promotion through locked benchmarks.

Primary metric:

**worst-generator Recall @ 1% verified-human FPR**.

Required ablations show each stream's contribution. Aggregate mean alone is insufficient.

Exit gate: calibrated fusion improves the best single-stream operating point or is rejected.

## P3 — Product integration

### #88 Runtime / CLI / GUI / history

Only after P0–P2 detector gates pass:
- local CLI/export;
- GUI evidence/uncertainty view;
- timestamp timeline;
- batch/Safe Stop;
- model/calibration identity in history;
- sequential VRAM ownership;
- integration with Resource Monitor / future ModelRuntimeManager.

Runtime gates:

```text
normal target peak VRAM < 8 GB
hard promotion gate      < 11 GB
```

Origin backend unavailable/failed must not break ordinary Analyze.

## Dataset strategy

Use separate partitions for:

1. **Verified Human** — provenance-backed, stratified controls.
2. **Known AI** — multiple generator families and versions.
3. **External unseen** — held out from all training/fitting.
4. **Project-owned real-world AI** — raw downloads, WAV, mastered variants and stem recombinations with explicit lineage.
5. **Content-matched controls** where possible to reduce genre/era/mastering confounds.

Never automatically classify the existing general Genre_test catalog as human training truth.

## Resource strategy

Do not run multiple duplicate heavy backbones simultaneously.

Preferred sequence:

```text
CPU Fourier
 -> compact CQT CNN
 -> existing MERT 95M segment extraction
 -> lightweight sequence/novelty/attribution heads
 -> CPU/lightweight calibrated fusion
```

Reuse cached MERT embeddings where preprocessing identities match.

## Promotion policy

A stream is promoted only when it improves one or more of:

- worst-generator Recall@1%FPR;
- verified-human per-stratum FPR;
- calibration;
- transformation robustness;
- uncertainty resolution;

without unacceptable regressions or runtime cost.

## Merge policy

Every issue/PR in this roadmap follows the repository rule: **no merge without explicit MTD**.
