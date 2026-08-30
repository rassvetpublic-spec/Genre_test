# MFCC Timbral Retrieval Baseline

Status: **benchmark-only / v0.5 P1**  
Issue: **#139**  
Related: **#33, #36, #44, #137**

## Purpose

Genre_test uses CLaMP 3 / MERT for semantic and multilingual retrieval. The MFCC baseline is deliberately narrower: it provides a small, deterministic, model-free **timbral similarity** representation that can be benchmarked against learned embeddings.

It is not:

- a replacement for CLaMP/MERT;
- a replacement for MAEST or AST;
- a genre classifier;
- a calibrated relevance probability;
- evidence of AI/generated origin;
- permission to mix MFCC and CLaMP scores with arbitrary weights.

## Source-of-knowledge registry

The external evidence and its limits are tracked in [`MFCC_SOURCE_REGISTRY.md`](MFCC_SOURCE_REGISTRY.md).

That registry separates:

```text
PRIMARY DOC / PRIMARY RESEARCH
UPSTREAM CODE
COMMUNITY OBSERVATION
PROJECT DECISION
```

Reddit/community material is hypothesis-generating only. It cannot supply production thresholds, fusion weights, or scientific truth without project-owned validation.

## Baseline V2

`mfcc-timbre78` uses only dependencies already present in Genre_test.

```text
input: mono 22.05 kHz
analysis level: RMS normalized to 0.1
FFT: 2048
hop: 512
Mel bands: 128

20 MFCC      -> mean + std -> 40 values
12 chroma    -> mean + std -> 24 values
7 contrast   -> mean + std -> 14 values
                               ---------
                               78 values

float32 -> L2 normalization
```

The fixed RMS analysis level prevents a pure global gain change from masquerading as timbral distance through MFCC coefficient 0. Effectively silent inputs are rejected instead of creating a misleading normalized vector.

Backend identity:

```text
backend_name: mfcc-timbre78
backend_version: 2
preprocessing_version:
  mfcc20-chroma12-contrast7-meanstd-sr22050-mono-nfft2048-hop512-
  rms0.1-librosa-<version>-numpy-<version>-scipy-<version>-v2
embedding_dim: 78
normalization: l2
```

The runtime Librosa/NumPy/SciPy versions are part of `preprocessing_version` and therefore the backend fingerprint. Environments that may produce incompatible vectors do not silently share one cache/index identity; a changed extractor runtime requires a different fingerprint and re-embedding.

Full-track and explicit segment embeddings use the existing `EmbeddingIdentity` contract. A segment requires both `start_s` and `end_s`; bounds outside the decoded source are rejected rather than silently clipped.

## Why this baseline exists

A useful external implementation pattern is [`horacio/simil`](https://github.com/horacio/simil), which exposes a lightweight local music-similarity path using MFCC + chroma + spectral contrast alongside learned alternatives. The useful engineering idea is not to copy its complete policy, but to keep a cheap model-free comparator available.

Librosa supplies the required feature extractors:

- [`librosa.feature.mfcc`](https://librosa.org/doc/latest/generated/librosa.feature.mfcc.html)
- [`librosa.feature.chroma_stft`](https://librosa.org/doc/latest/generated/librosa.feature.chroma_stft.html)
- [`librosa.feature.spectral_contrast`](https://librosa.org/doc/latest/generated/librosa.feature.spectral_contrast.html)

Community discussions around audio-similarity grading repeatedly make the same practical point: MFCC-style features and learned embeddings can be complementary, but a combined score is not meaningful until the target notion of similarity is defined and calibrated. Genre_test therefore keeps MFCC similarity independent at first.

## Benchmark contract with #36

The first required comparison is:

```text
A. CLaMP/MERT semantic retrieval
B. MFCC timbral baseline
```

Evaluate both on the existing reviewed categories from #36, especially:

- exact / near duplicate;
- remix / original;
- same subgenre;
- same broad family but different style;
- similar mood/energy but different genre;
- vocal similarity;
- instrumentation similarity;
- deliberately unrelated negatives.

Use the existing retrieval metrics:

- Precision@K;
- Recall@K;
- MRR;
- nDCG@K;
- repeatability;
- latency and throughput.

Robustness fixtures should explicitly include global gain variants so the V2 level policy stays covered by project-owned evidence.

Do not introduce:

```text
combined_score = a * clamp + b * mfcc
```

until project-owned benchmark evidence justifies both the fusion rule and its weights.

## Relationship to #33

Representative-segment selection in #33 remains based on the versioned retrieval embedding policy. MFCC may later be reported as independent timbral evidence for a segment, but this issue does not silently replace the current centroid/cosine representative policy.

## Relationship to #44

MFCC is potentially useful for structural novelty and timbral change-point evidence, but that is separate from this V2 full/segment fingerprint. #44 remains responsible for conservative tempo/structure change semantics.

The source registry records Librosa examples for beat-synchronous MFCC aggregation and MFCC-based local path similarity as future research evidence only; they do not graduate automatically into #44 production logic.

## Relationship to #137

MFCC temporal derivatives and trajectory statistics belong to #137, including experiments such as:

- MFCC delta variance;
- MFCC delta-2 variance;
- trajectory path length;
- trajectory acceleration statistics.

Those signals must not be interpreted as AI-origin truth. #139 intentionally implements only the static timbral retrieval baseline.

## Review findings and resolution

Two review blockers from the original PR #140 are resolved in V2:

1. **Gain dependence / MFCC coefficient 0** — input is normalized to a fixed RMS analysis level before MFCC/chroma/contrast extraction, and unit tests compare the same synthetic material at multiple global gains.
2. **Extractor implementation identity** — Librosa/NumPy/SciPy runtime versions are incorporated into `preprocessing_version`, which feeds the existing backend fingerprint and prevents silent cache/index mixing across different extractor runtimes.

These fixes remove the implementation blockers; they do **not** prove that MFCC78 adds useful retrieval relevance. That remains a #36 benchmark question.

## Expected storage cost

For approximately 10.5k tracks:

```text
10,500 * 78 * 4 bytes ~= 3.1 MiB raw float32 vectors
```

This is small enough for exact cosine ranking and does not justify an ANN/vector-database dependency.

## Graduation rule

The baseline may graduate from benchmark utility only if #36 demonstrates incremental value. Valid outcomes include:

- useful independent `Timbral similarity` evidence;
- useful reranking input after calibration;
- benchmark-only diagnostic value;
- rejection/removal if it adds no measurable value.

`BYPASS`/no-use is therefore a valid result for this feature as well.
