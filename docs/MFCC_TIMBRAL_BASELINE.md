# MFCC Handcrafted Acoustic Retrieval Baseline

Status: **benchmark-only / v0.5 P1**
Issue: **#139**
Related: **#33, #36, #44, #137**

The historical filename is retained for continuity, but V3 is explicitly a **handcrafted acoustic** representation, not a timbre-only axis.

## Purpose

Genre_test uses CLaMP 3 / MERT for semantic and multilingual retrieval. This baseline is deliberately narrower: it provides a small, deterministic, model-free acoustic representation that can be benchmarked against learned embeddings.

It combines:

- MFCC statistics: timbral/spectral-envelope evidence;
- chroma statistics: pitch-class/harmonic evidence;
- spectral-contrast statistics: spectral-distribution evidence.

It is not:

- a replacement for CLaMP/MERT;
- a replacement for MAEST or AST;
- a pure timbral axis;
- a genre classifier;
- a calibrated relevance probability;
- evidence of AI/generated origin;
- permission to mix handcrafted and learned scores with arbitrary weights.

## Source-of-knowledge registry

External evidence and limits are tracked in [`MFCC_SOURCE_REGISTRY.md`](MFCC_SOURCE_REGISTRY.md).

The registry separates:

```text
PRIMARY DOC / PRIMARY RESEARCH
UPSTREAM CODE
COMMUNITY OBSERVATION
PROJECT DECISION
```

Reddit/community material is hypothesis-generating only. It cannot supply production thresholds, fusion weights, or scientific truth without project-owned validation.

## Baseline V3

`mfcc-acoustic78` uses dependencies already present in Genre_test.

```text
input: mono 22.05 kHz exactly
minimum usable RMS: -80 dBFS
analysis level after gate: RMS normalized to 0.1
FFT: 2048
hop: 512
Mel bands: 128

20 MFCC      -> mean + std -> 40 values -> family L2
12 chroma    -> mean + std -> 24 values -> family L2
7 contrast   -> mean + std -> 14 values -> family L2
                                             ---------
                                             78 values

equal-norm feature families -> concatenate -> global L2 -> float32
```

### Why the V3 gates exist

A fixed RMS analysis level prevents pure global gain from masquerading as acoustic distance through MFCC coefficient 0.

The usable-signal gate is applied **before** RMS amplification. Inputs below `-80 dBFS RMS` are rejected so ordinary dither/codec/quantization residue is not amplified into a confident unit vector. This threshold is benchmark policy and is part of the fingerprint; #36 may later justify a revision.

The analysis sample rate is strict. Public extraction and decoded input must both be `22_050 Hz`, matching the rate encoded in backend identity.

MFCC, chroma and spectral contrast have different numerical scales. V3 L2-normalizes each family block before concatenation, giving all three families equal vector-norm weight. This makes the weighting policy explicit; it does **not** claim equal weighting is optimal.

Because chroma is present, transposition/key/harmony can affect the score independently of timbre. #36 must interpret this backend as a handcrafted acoustic comparator rather than `Timbral similarity` ground truth.

Backend identity:

```text
backend_name: mfcc-acoustic78
backend_version: 3
preprocessing_version:
  mfcc20-chroma12-contrast7-meanstd-sr22050-mono-nfft2048-hop512-
  rms0.1-minrms-80dbfs-familyl2equal-
  librosa-<version>-numpy-<version>-scipy-<version>-v3
embedding_dim: 78
normalization: family-l2-equal+global-l2
```

Librosa/NumPy/SciPy versions are part of `preprocessing_version` and therefore the backend fingerprint. Incompatible extractor runtimes or preprocessing policies do not silently share one cache/index identity; a changed identity requires re-embedding.

Full-track and explicit segment embeddings use the existing `EmbeddingIdentity` contract. A segment requires both `start_s` and `end_s`; bounds outside the decoded source are rejected rather than silently clipped.

## Why this baseline exists

A useful upstream implementation pattern is [`horacio/simil`](https://github.com/horacio/simil), which exposes a lightweight local music-similarity path using MFCC + chroma + spectral contrast alongside learned alternatives. Genre_test borrows only the idea of a cheap independent handcrafted comparator, not its complete policy or implicit weighting.

Librosa supplies the required feature extractors:

- [`librosa.feature.mfcc`](https://librosa.org/doc/latest/generated/librosa.feature.mfcc.html)
- [`librosa.feature.chroma_stft`](https://librosa.org/doc/latest/generated/librosa.feature.chroma_stft.html)
- [`librosa.feature.spectral_contrast`](https://librosa.org/doc/latest/generated/librosa.feature.spectral_contrast.html)

## Benchmark contract with #36

The first required comparison is:

```text
A. CLaMP/MERT semantic retrieval
B. ACOUSTIC78 handcrafted retrieval
```

Evaluate both on reviewed categories from #36, especially:

- exact / near duplicate;
- remix / original;
- same subgenre;
- same broad family but different style;
- similar mood/energy but different genre;
- vocal similarity;
- instrumentation similarity;
- same/different key or harmony where useful for chroma ablation;
- deliberately unrelated negatives.

Use existing retrieval metrics:

- Precision@K;
- Recall@K;
- MRR;
- nDCG@K;
- repeatability;
- latency and throughput.

Robustness fixtures should include:

- global gain variants;
- near-silence/low-level controls;
- codec/mastering variants where relevant;
- transposed or harmony-controlled variants if #36 wants to quantify chroma influence.

Do not introduce:

```text
combined_score = a * clamp + b * acoustic78
```

until project-owned benchmark evidence justifies both the fusion rule and its weights.

## Relationship to #33

Representative-segment selection in #33 remains based on the versioned retrieval embedding policy. ACOUSTIC78 may later be reported as independent evidence for a segment, but this issue does not silently replace the current centroid/cosine representative policy.

## Relationship to #44

MFCC is potentially useful for structural novelty and acoustic change-point evidence, but that is separate from this V3 full/segment fingerprint. #44 remains responsible for conservative tempo/structure change semantics.

The source registry records Librosa examples for beat-synchronous MFCC aggregation and MFCC-based local path similarity as future research evidence only; they do not graduate automatically into #44 production logic.

## Relationship to #137

MFCC temporal derivatives and trajectory statistics belong to #137, including experiments such as:

- MFCC delta variance;
- MFCC delta-2 variance;
- trajectory path length;
- trajectory acceleration statistics.

Those signals must not be interpreted as AI-origin truth. #139 implements only the static handcrafted acoustic retrieval baseline.

## Review findings and V3 resolution

The baseline now explicitly resolves the material review findings accumulated through #140/#143/#172:

1. **Global gain dependence** — fixed RMS analysis normalization plus gain-variant tests.
2. **Extractor-version drift** — Librosa/NumPy/SciPy versions in the fingerprint.
3. **Implicit family weighting** — each feature-family mean/std block receives L2 normalization before concatenation, followed by global L2.
4. **Timbre-only overclaim** — backend/documentation renamed to handcrafted acoustic because chroma carries pitch-class/harmonic information.
5. **Near-silence amplification** — inputs below `-80 dBFS RMS` are rejected before normalization and covered by tests.
6. **Sample-rate identity mismatch** — extraction and decoder boundaries require exactly `22_050 Hz`, matching the fingerprint.

These fixes remove implementation/methodology ambiguity; they do **not** prove that ACOUSTIC78 improves retrieval relevance. That remains a #36 benchmark question.

## Expected storage cost

For approximately 10.5k tracks:

```text
10,500 * 78 * 4 bytes ~= 3.1 MiB raw float32 vectors
```

This is small enough for exact cosine ranking and does not justify an ANN/vector-database dependency.

## Graduation rule

The baseline may graduate from benchmark utility only if #36 demonstrates incremental value. Valid outcomes include:

- useful independent handcrafted acoustic evidence;
- useful reranking input after calibration;
- benchmark-only diagnostic value;
- rejection/removal if it adds no measurable value.

`BYPASS`/no-use is a valid result.
