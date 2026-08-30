# MFCC Handcrafted Acoustic Source-of-Knowledge Registry

Status: **research evidence / Issue #139**
Related: **#33, #36, #44, #137**

## Purpose

This registry records the external evidence behind the model-free MFCC/chroma/spectral-contrast retrieval baseline, the limits of each source, and the project decisions derived from them.

Evidence flow:

```text
source fact / external observation
        -> project hypothesis
        -> project-owned benchmark evidence
        -> implementation or product decision
```

A Reddit comment or third-party implementation is not scientific ground truth. Community material may motivate a test, but only project-owned benchmark evidence may justify calibration, score fusion, production ranking, or semantic claims.

## Evidence classes

- **PRIMARY DOC** — official library/API documentation.
- **PRIMARY RESEARCH** — research paper or equivalent primary publication.
- **UPSTREAM CODE** — inspectable third-party implementation pattern.
- **COMMUNITY OBSERVATION** — Reddit/community experience; hypothesis-generating only.
- **PROJECT DECISION** — a Genre_test engineering decision derived from evidence and current architecture.

---

## S1 — `horacio/simil`: model-free music-similarity baseline

Type: **UPSTREAM CODE**
Source: https://github.com/horacio/simil

Relevant behavior:

- provides MFCC as a fast model-free music-similarity path;
- uses 20 MFCC coefficients, 12 chroma bins and 7 spectral-contrast values;
- aggregates mean + standard deviation to 78 dimensions;
- keeps MFCC, Discogs-EffNet and CLAP as separate embedding spaces;
- presents learned music embeddings as stronger for semantic/music-aware similarity.

Genre_test use:

- motivates a cheap independent handcrafted acoustic comparator;
- motivates the initial `20 MFCC + 12 chroma + 7 contrast -> mean/std -> 78D` shape;
- does not prove those parameters or their relative weighting are optimal for Genre_test.

---

## S2 — Librosa MFCC API

Type: **PRIMARY DOC**
Source: https://librosa.org/doc/main/api/generated/librosa.feature.mfcc.html

Relevant facts:

- MFCC output depends on coefficient count, DCT type/normalization, liftering and Mel-spectrogram configuration;
- multi-channel behavior can depend on peak loudness across channels and differ from independent channel calculation.

Genre_test use:

- the baseline is intentionally mono;
- stereo/phase information remains a separate TechnicalProfile concern;
- MFCC parameters and extractor implementation identity belong in the backend fingerprint.

---

## S3 — Essentia MFCC reference

Type: **PRIMARY DOC**
Source: https://essentia.upf.edu/reference/streaming_MFCC.html

Relevant facts:

Essentia exposes materially different MFCC choices including:

- Mel-band count and frequency bounds;
- coefficient count;
- DCT type;
- liftering;
- log-compression policy;
- magnitude vs power spectrum;
- Mel warping and filter normalization;
- sample rate.

Genre_test use:

- there is no safe identity `backend=mfcc` without preprocessing details;
- incompatible extractor implementations must never silently share one cache/index identity;
- Essentia and Librosa vectors are not assumed numerically interchangeable.

---

## S4 — Librosa tutorial: MFCC deltas and beat-synchronous aggregation

Type: **PRIMARY DOC**
Source: https://librosa.org/doc/0.10.2/tutorial.html

Relevant example:

```text
MFCC
 -> first-order delta
 -> stack
 -> synchronize / aggregate between beat frames
```

Genre_test use:

- supports future research under #44/#137 where temporal MFCC evidence is synchronized to musical time;
- candidate research features include MFCC delta/delta-2 and beat-synchronous summaries.

Boundary:

- these temporal features are not part of the static 78D retrieval baseline;
- no temporal derivative is interpreted as AI-origin truth.

---

## S5 — Librosa Laplacian segmentation example

Type: **PRIMARY DOC**
Source: https://librosa.org/doc/main/auto_tutorials/03-advanced/plot_segmentation.html

Relevant behavior:

- beat-synchronous MFCCs contribute to local path similarity;
- successive beat distance from MFCC change is combined with recurrence information.

Genre_test use:

- supports the hypothesis that MFCC trajectories may help conservative acoustic change-point evidence for #44;
- does not justify Verse/Chorus/Bridge/Drop naming.

---

## S6 — Reddit r/audioengineering: CLAP + MFCC fusion requires a defined target

Type: **COMMUNITY OBSERVATION**
Source: https://www.reddit.com/r/audioengineering/comments/1rkldh7/audio_similarity_grading_question/

Useful observation:

Handcrafted features and learned embeddings can both be useful, but a combined score is not meaningful until the target notion of similarity is defined.

Genre_test interpretation:

```text
semantic similarity
!= handcrafted acoustic similarity
!= structural novelty
```

Benchmark CLaMP/MERT and the handcrafted baseline independently in #36 before any score fusion. No Reddit weights or thresholds are adopted.

---

## S7 — Reddit r/DSP: MFCC matching robustness under noise/hum

Type: **COMMUNITY OBSERVATION**
Source: https://www.reddit.com/r/DSP/comments/1j52go2

Useful observation:

A hobby speaker-verification implementation using MFCC/delta matching reportedly degrades strongly when noise/hum is added.

Genre_test interpretation:

- robustness must be measured rather than assumed;
- #36 fixtures should include gain changes, mild noise, codec variants and mastering variants where relevant.

Boundary: speech verification is not music retrieval; this source motivates tests only.

---

## S8 — Reddit r/MachineLearning: learned embeddings versus handcrafted audio features

Type: **COMMUNITY OBSERVATION**
Source: https://www.reddit.com/r/MachineLearning/comments/1chmi0e

Useful observation:

A practitioner discussion reports stronger in-the-wild generalization from learned audio embeddings than from traditional MFCC/filterbank/prosodic features in their task.

Genre_test interpretation:

- consistent with CLaMP/MERT remaining the learned semantic retrieval path;
- the handcrafted baseline remains a comparator/complement, not a replacement simply because it is cheaper.

Boundary: anecdotal and not a music-retrieval benchmark.

---

## S9 — GTZAN fault analysis

Type: **PRIMARY RESEARCH**
Source: Bob L. Sturm, *The GTZAN dataset: Its contents, its faults, their effects on evaluation, and its future use*
URL: https://arxiv.org/abs/1306.1461

Relevant findings:

- GTZAN contains repetitions, mislabelings and distortions;
- these faults affect interpretation of music-genre-recognition evaluation.

Genre_test interpretation:

- reject the shortcut `MFCC -> CNN/SVM -> GTZAN headline accuracy -> replace MAEST`;
- MAEST/AST production classification stays separate from handcrafted retrieval research;
- any future classifier change requires modern project-owned reviewed fixtures.

---

## Project-owned conclusions

### C1 — MFCC/chroma/contrast is complementary acoustic evidence

```text
MAEST       -> fine-style / genre evidence
AST         -> semantic evidence
CLaMP/MERT  -> semantic / multilingual retrieval
ACOUSTIC78  -> cheap handcrafted acoustic baseline
MFCC temporal research -> possible structure/artifact evidence (#44/#137)
```

Because the 78D representation contains chroma, it is **not a timbre-only axis**. Chroma contributes pitch-class/harmonic information and can respond to key/harmony/transposition. The backend and documentation therefore use `mfcc-acoustic78` / handcrafted acoustic terminology.

### C2 — Similarity axes remain separate until calibrated

No production formula such as:

```text
combined = 0.8 * clamp + 0.2 * acoustic78
```

is allowed without #36 project-owned relevance evidence.

### C3 — Implementation identity is part of vector compatibility

The current V3 fingerprint records:

- mono 22.05 kHz preprocessing and strict sample-rate enforcement;
- FFT/hop and feature counts;
- fixed RMS analysis-level policy;
- minimum usable input RMS (`-80 dBFS`);
- mean/std aggregation policy;
- equal feature-family norm weighting before final L2 normalization;
- Librosa version;
- NumPy version;
- SciPy version;
- baseline algorithm revision.

A changed extractor runtime or preprocessing contract therefore creates a different fingerprint and requires re-embedding rather than silently mixing vectors.

### C4 — Global-gain dependence is controlled

MFCC coefficient 0 carries log-energy information, so a pure global gain change can rotate a raw concatenated vector even after final L2 normalization.

Resolution:

- reject inputs below the V3 usable-signal gate;
- normalize valid input to fixed RMS `0.1` before extraction;
- retain all 20 MFCC coefficients;
- test quieter and louder copies of identical material.

This controls global-gain sensitivity for the benchmark. It does not prove retrieval value; #36 still owns relevance evidence.

### C5 — Extractor-version and sample-rate drift are controlled

Resolution:

- include Librosa/NumPy/SciPy runtime versions in `preprocessing_version`;
- require the encoded `22_050 Hz` analysis rate at both public extraction and decoder boundaries;
- because `preprocessing_version` contributes to `RetrievalBackendInfo.fingerprint`, incompatible runtimes/preprocessing policies no longer share the same embedding identity.

### C6 — Feature-family scale is explicit in V3

MFCC, chroma and spectral-contrast statistics use different numerical scales. Raw concatenation followed by one global L2 normalization would create an implicit and undocumented weighting policy.

V3 therefore:

```text
MFCC mean/std block      -> block L2
chroma mean/std block    -> block L2
contrast mean/std block  -> block L2
three equal-norm blocks  -> concatenate -> final L2
```

Each family contributes equal vector norm before any future #36 calibration. This is a declared benchmark policy, not a claim that equal weighting is optimal.

### C7 — Practical near-silence is rejected before amplification

Exact-zero detection is insufficient because dither, codec residue or quantization noise can have nonzero RMS. V3 rejects inputs below `-80 dBFS RMS` before scaling to the target analysis level. The threshold is part of the fingerprint and remains benchmark policy subject to #36 corpus validation.

---

## Benchmark hypotheses — not product claims

| Retrieval relation | ACOUSTIC78 expected utility | CLaMP/MERT expected utility |
|---|---:|---:|
| exact / near duplicate | high | high |
| gain variant | high after V3 level normalization | high |
| mastering / codec variant | benchmark required | high / benchmark required |
| similar timbral balance | high | medium/high |
| same key/harmony | can influence score via chroma | semantic relevance varies |
| instrumentation similarity | medium/high | high |
| same subgenre | low/medium | high |
| broad semantic genre | low/medium | high |
| mood / descriptive semantics | low | high |
| Russian text -> music | none | high |

These are hypotheses, not acceptance thresholds.

## Graduation rule

The handcrafted baseline may graduate from benchmark utility only when:

1. source facts remain traceable to this registry;
2. preprocessing, weighting and extractor runtime identity are versioned;
3. gain, near-silence, sample-rate and family-weighting findings remain covered by tests;
4. #36 measures real retrieval quality and perturbation robustness;
5. any future #44/#137 temporal use receives independent DSP/audio-science validation;
6. unsupported community claims remain hypotheses, not product truth.

`BYPASS` / no-use is a valid final outcome if #36 shows no incremental value.
