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

It is not a replacement for CLaMP/MERT, MAEST or AST; not a pure timbral axis; not a genre classifier; not a calibrated relevance probability; not evidence of AI/generated origin; and not permission to mix handcrafted and learned scores with arbitrary weights.

## Source-of-knowledge registry

External evidence and limits are tracked in [`MFCC_SOURCE_REGISTRY.md`](MFCC_SOURCE_REGISTRY.md). Implementation-derived upstream evidence is revision-pinned. The initial 20/12/7 + mean/std shape was verified against `horacio/simil` commit `cb6da9ccd5ea6c675b66ad8d3b378f0a6ca322de`, file `simil/embedders/mfcc.py`.

Reddit/community material remains hypothesis-generating only. It cannot supply production thresholds, fusion weights, or scientific truth without project-owned validation.

## Baseline V3

`mfcc-acoustic78` uses a dedicated, fingerprinted preprocessing path rather than the shared variable decoder fallback:

```text
input file
 -> SoundFile / libsndfile decode to float32
 -> explicit channel mean to mono
 -> SciPy resample_poly to 22.05 kHz when needed
 -> usable-signal gate: -80 dBFS RMS
 -> analysis RMS normalization to 0.1
 -> MFCC / chroma / spectral contrast
```

Files unsupported by the installed fingerprinted SoundFile/libsndfile stack fail this optional benchmark independently; the backend does not silently switch to audioread/FFmpeg and reuse the same vector identity.

Feature construction:

```text
analysis rate: 22.05 kHz exactly
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

The feature-extraction sample rate is strict and always `22_050 Hz`, matching backend identity. Source-rate conversion is performed only through the fingerprinted SciPy `resample_poly` path.

MFCC, chroma and spectral contrast have different numerical scales. V3 L2-normalizes each family block before concatenation, giving all three families equal vector-norm weight. This makes the weighting policy explicit; it does **not** claim equal weighting is optimal.

Because chroma is present, transposition/key/harmony can affect the score independently of timbre. #36 must interpret this backend as a handcrafted acoustic comparator rather than `Timbral similarity` ground truth.

Backend identity includes:

```text
backend_name: mfcc-acoustic78
backend_version: 3
sample/decode policy:
  soundfile-libsndfile-float32-mono-mean-resample-poly
feature policy:
  mfcc20-dct2-ortho-lifter0-mels128-power2
  chroma12
  contrast7-fmin200-quantile0.02-linearfalse
  meanstd-sr22050-mono-nfft2048-hop512
  rms0.1-minrms-80dbfs-familyl2equal
runtime identity:
  librosa-<version>-numpy-<version>-scipy-<version>
  soundfile-<version>-libsndfile-<version>
embedding_dim: 78
normalization: l2
```

Every explicit extractor parameter that can change vector compatibility is part of this feature policy. Code and fingerprint use the same named constants for those settings, so changing MFCC DCT/norm/lifter/Mel/power, chroma count, spectral-contrast band/fmin/quantile/linear, sample rate, FFT or hop changes the preprocessing identity and requires re-embedding.

`normalization: l2` is the shared `RetrievalBackendInfo` contract for the final vector. Equal-norm family weighting is part of the fingerprinted preprocessing policy (`familyl2equal`), not a separate normalization enum.

These fields feed `preprocessing_version` and therefore `RetrievalBackendInfo.fingerprint`. A decoder, resampler, extractor runtime or preprocessing-policy change creates a distinct vector identity and requires re-embedding.

Full-track and explicit segment embeddings use the existing `EmbeddingIdentity` contract. A segment requires both `start_s` and `end_s`; bounds outside the decoded source are rejected rather than silently clipped.

## Why this baseline exists

The pinned upstream `horacio/simil` implementation demonstrates a lightweight local music-similarity path using 20 MFCC + 12 chroma + 7 spectral-contrast features with mean/std aggregation. Genre_test borrows only the idea of a cheap independent handcrafted comparator, not its clip-selection, decode policy or implicit raw-feature weighting.

Librosa supplies the feature extractors:

- `librosa.feature.mfcc`
- `librosa.feature.chroma_stft`
- `librosa.feature.spectral_contrast`

## Benchmark contract with #36

The first required comparison is:

```text
A. CLaMP/MERT semantic retrieval
B. ACOUSTIC78 handcrafted retrieval
```

Evaluate both on reviewed categories from #36, especially exact/near duplicates, remix/original, subgenre/family relations, mood/energy contrasts, vocal/instrumentation similarity, same/different key or harmony for chroma ablation, and unrelated negatives.

Use Precision@K, Recall@K, MRR, nDCG@K, repeatability, latency and throughput.

Robustness fixtures should include global gain variants, near-silence controls, decode/sample-rate controls, codec/mastering variants where supported, and transposed/harmony-controlled variants if #36 wants to quantify chroma influence.

Do not introduce:

```text
combined_score = a * clamp + b * acoustic78
```

until project-owned benchmark evidence justifies both the fusion rule and its weights.

## Relationship to #33 / #44 / #137

- #33 representative-segment policy is not replaced; ACOUSTIC78 may only add independent evidence later.
- #44 remains responsible for conservative tempo/structure change semantics; beat-synchronous MFCC ideas are research evidence only.
- #137 owns MFCC temporal derivatives/trajectory statistics. They must not be interpreted as AI-origin truth.

## Review findings and V3 resolution

The baseline resolves the material findings accumulated through #140/#143/#172:

1. **Global gain dependence** — fixed RMS analysis normalization plus gain-variant tests.
2. **Extractor-version drift** — Librosa/NumPy/SciPy versions in the fingerprint.
3. **Implicit family weighting** — family-level L2 before concatenation plus global L2.
4. **Timbre-only overclaim** — renamed to handcrafted acoustic because chroma carries harmonic information.
5. **Near-silence amplification** — `-80 dBFS RMS` gate before normalization.
6. **Sample-rate identity mismatch** — feature extraction fixed at `22_050 Hz`.
7. **Variable decoder/resampler identity** — dedicated SoundFile/libsndfile + explicit mono mean + SciPy `resample_poly`; runtime versions/policy are fingerprinted and no silent FFmpeg fallback is allowed.
8. **Mutable upstream evidence** — the upstream implementation supporting the initial 78D shape is pinned to an inspected commit and file path in the source registry.
9. **Shared retrieval normalization contract** — final vector identity remains `normalization="l2"`; family equalization remains a preprocessing/fingerprint detail.
10. **Extractor-parameter identity completeness** — every explicit MFCC/chroma/spectral-contrast parameter used by V3 is now part of the fingerprinted feature policy and regression-tested.

These fixes remove implementation/methodology ambiguity; they do **not** prove that ACOUSTIC78 improves retrieval relevance. That remains a #36 benchmark question.

## Expected storage cost

For approximately 10.5k tracks:

```text
10,500 * 78 * 4 bytes ~= 3.1 MiB raw float32 vectors
```

This is small enough for exact cosine ranking and does not justify an ANN/vector-database dependency.

## Graduation rule

The baseline may graduate from benchmark utility only if #36 demonstrates incremental value. Valid outcomes include useful independent handcrafted acoustic evidence, calibrated reranking input, benchmark-only diagnostic value, or rejection/removal if it adds no measurable value.

`BYPASS`/no-use is a valid result.
