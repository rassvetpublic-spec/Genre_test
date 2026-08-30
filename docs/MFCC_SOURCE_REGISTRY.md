# MFCC Source-of-Knowledge Registry

Status: **research evidence / Issue #139**  
Related: **#33, #36, #44, #137**

## Purpose

This registry records the external evidence behind the model-free MFCC timbral-retrieval baseline, the limits of each source, and the project decisions derived from them.

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

- motivates a cheap independent timbral comparator;
- motivates the initial `20 MFCC + 12 chroma + 7 contrast -> mean/std -> 78D` shape;
- does not prove those parameters are optimal for Genre_test.

---

## S2 — Librosa MFCC API

Type: **PRIMARY DOC**  
Source: https://librosa.org/doc/main/api/generated/librosa.feature.mfcc.html

Relevant facts:

- MFCC output depends on coefficient count, DCT type/normalization, liftering and Mel-spectrogram configuration;
- multi-channel behavior can depend on peak loudness across channels and differ from independent channel calculation.

Genre_test use:

- `mfcc-timbre78` is intentionally mono;
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

- supports future research under #44/#137 where temporal timbral evidence is synchronized to musical time;
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

- supports the hypothesis that MFCC trajectories may help conservative timbral change-point evidence for #44;
- does not justify Verse/Chorus/Bridge/Drop naming.

---

## S6 — Reddit r/audioengineering: CLAP + MFCC fusion requires a defined target

Type: **COMMUNITY OBSERVATION**  
Source: https://www.reddit.com/r/audioengineering/comments/1rkldh7/audio_similarity_grading_question/

Useful observation:

MFCC-style and learned embeddings can both be useful, but a combined score is not meaningful until the target notion of similarity is defined.

Genre_test interpretation:

```text
semantic similarity
!= timbral similarity
!= structural novelty
```

Benchmark CLaMP/MERT and MFCC independently in #36 before any score fusion. No Reddit weights or thresholds are adopted.

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
- MFCC remains a comparator/complement, not a replacement simply because it is cheaper.

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
- MAEST/AST production classification stays separate from MFCC retrieval research;
- any future classifier change requires modern project-owned reviewed fixtures.

---

## Project-owned conclusions

### C1 — MFCC is complementary evidence

```text
MAEST       -> fine-style / genre evidence
AST         -> semantic evidence
CLaMP/MERT  -> semantic / multilingual retrieval
MFCC78      -> cheap timbral retrieval baseline
MFCC temporal research -> possible structure/artifact evidence (#44/#137)
```

MFCC does not replace MAEST, AST or CLaMP/MERT.

### C2 — Similarity axes remain separate until calibrated

No production formula such as:

```text
combined = 0.8 * clamp + 0.2 * mfcc
```

is allowed without #36 project-owned relevance evidence.

### C3 — Implementation identity is part of vector compatibility

The current V2 fingerprint records:

- mono 22.05 kHz preprocessing;
- FFT/hop and feature counts;
- fixed RMS analysis-level policy;
- aggregation policy;
- Librosa version;
- NumPy version;
- SciPy version;
- baseline algorithm revision.

A changed extractor runtime therefore creates a different fingerprint and requires re-embedding rather than silently mixing vectors.

### C4 — Gain dependence review finding is resolved in V2

The original PR #140 review correctly identified that MFCC coefficient 0 carries log-energy information and a pure global gain change could rotate the final 78D vector even after L2 normalization.

Resolution:

- normalize valid non-silent input to a fixed RMS analysis level (`0.1`) before extraction;
- retain all 20 MFCC coefficients;
- add gain-variant unit tests for quieter and louder copies of identical material;
- reject effectively silent inputs instead of manufacturing a normalized timbral vector.

This resolves the implementation blocker. It does not prove retrieval value; #36 still owns benchmark evidence.

### C5 — Extractor-version drift review finding is resolved in V2

The original PR #140 review also identified that broad dependency ranges can resolve different Librosa/NumPy/SciPy implementations.

Resolution:

- include those runtime versions in `preprocessing_version`;
- because `preprocessing_version` contributes to `RetrievalBackendInfo.fingerprint`, incompatible runtimes no longer share the same embedding identity;
- a version change therefore forces separate cache/index identity and re-embedding semantics.

---

## Benchmark hypotheses — not product claims

| Retrieval relation | MFCC78 expected utility | CLaMP/MERT expected utility |
|---|---:|---:|
| exact / near duplicate | high | high |
| gain variant | high after V2 level normalization | high |
| mastering / codec variant | benchmark required | high / benchmark required |
| similar timbral balance | high | medium/high |
| instrumentation similarity | medium/high | high |
| same subgenre | low/medium | high |
| broad semantic genre | low/medium | high |
| mood / descriptive semantics | low | high |
| Russian text -> music | none | high |

These are hypotheses, not acceptance thresholds.

## Graduation rule

MFCC knowledge is integrated as a benchmark utility when:

1. source facts remain traceable to this registry;
2. implementation parameters and extractor runtime identity are versioned;
3. gain and version-drift implementation findings remain covered by tests;
4. #36 measures real retrieval quality and perturbation robustness;
5. any future #44/#137 temporal use receives independent DSP/audio-science validation;
6. unsupported community claims remain hypotheses, not product truth.

`BYPASS` / no-use is a valid final outcome if #36 shows no incremental value.
