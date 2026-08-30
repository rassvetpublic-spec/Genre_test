# MFCC Source-of-Knowledge Registry

Status: **research evidence / PR #140**  
Issue: **#139**  
Related: **#33, #36, #44, #137**

## Purpose

This file records the external evidence behind the MFCC timbral-retrieval baseline and the limits of what those sources justify.

The project separates:

```text
source fact / external observation
        -> project hypothesis
        -> project-owned benchmark evidence
        -> implementation or product decision
```

A Reddit comment or third-party implementation is not treated as scientific ground truth. It may motivate a test, but only project-owned benchmark evidence may justify calibration, score fusion, or production ranking changes.

## Evidence classes

- **PRIMARY DOC** — official library/API documentation or primary research paper.
- **UPSTREAM CODE** — inspectable third-party implementation pattern.
- **COMMUNITY OBSERVATION** — Reddit/community experience; hypothesis-generating only.
- **PROJECT DECISION** — a Genre_test engineering decision derived from evidence and current architecture.

---

## S1 — `horacio/simil`: model-free MFCC retrieval baseline

Type: **UPSTREAM CODE**  
Source: https://github.com/horacio/simil

Relevant upstream behavior:

- exposes MFCC as a fast, model-free music-similarity baseline;
- uses 20 MFCC coefficients, 12 chroma bins and 7 spectral-contrast values;
- aggregates each group with mean + standard deviation;
- produces a 78-dimensional vector;
- keeps MFCC, Discogs-EffNet and CLAP as incompatible embedding spaces rather than silently mixing them;
- describes MFCC quality as basic and learned music embeddings as better for music-aware similarity.

Genre_test use:

- validates the engineering usefulness of a cheap comparator with no model download;
- motivates the initial `20 MFCC + 12 chroma + 7 spectral contrast -> mean/std -> 78D` shape;
- does **not** establish that the same parameters are optimal for Genre_test.

Limitations:

- third-party implementation, not a benchmark on the Genre_test catalog;
- its track sampling policy and product goals are not automatically adopted;
- any copied parameter must still be versioned and tested locally.

---

## S2 — Librosa MFCC API: explicit MFCC parameterization and channel caveat

Type: **PRIMARY DOC**  
Source: https://librosa.org/doc/main/api/generated/librosa.feature.mfcc.html

Relevant facts:

- MFCC output depends on parameters such as `n_mfcc`, DCT type, DCT normalization, liftering and Mel-spectrogram configuration;
- current Librosa documentation explicitly supports multi-channel input;
- MFCC calculation for multi-channel audio can depend on peak loudness across channels and can differ from independent per-channel calculation.

Genre_test use:

- `mfcc-timbre78` is intentionally mono;
- stereo/phase information remains a separate TechnicalProfile concern rather than being folded into the timbral fingerprint;
- MFCC extraction parameters are part of preprocessing identity.

Limitations:

- library documentation defines behavior, not retrieval quality;
- version changes can alter implementation details or defaults, so extractor-library identity must be controlled.

---

## S3 — Essentia MFCC reference: there is no single universal MFCC implementation

Type: **PRIMARY DOC**  
Source: https://essentia.upf.edu/reference/streaming_MFCC.html

Relevant facts:

Essentia explicitly states that there is no single standard MFCC implementation and exposes materially different choices, including:

- number of Mel bands;
- number of coefficients;
- low/high frequency bounds;
- DCT type;
- liftering;
- log-compression type;
- magnitude vs power spectrum;
- Mel warping formula (`slaneyMel` vs `htkMel`);
- filter normalization;
- sample rate.

Genre_test use:

- an embedding cannot be identified only as `backend=mfcc`;
- the complete feature-extraction policy must be versioned strongly enough that incompatible vectors are never silently mixed;
- environment/library changes require either pinned implementations or a fingerprint change/re-embedding policy.

Limitations:

- Essentia and Librosa implementations are not assumed numerically interchangeable.

---

## S4 — Librosa tutorial: MFCC deltas and beat-synchronous aggregation

Type: **PRIMARY DOC**  
Source: https://librosa.org/doc/0.10.2/tutorial.html

Relevant example:

```text
MFCC
 -> first-order delta
 -> stack
 -> synchronize/aggregate between beat frames
```

The tutorial demonstrates `librosa.feature.delta` and `librosa.util.sync` for beat-synchronous feature aggregation.

Genre_test use:

- supports a future research path for #44/#137 where temporal timbral evidence is synchronized to musical time instead of reacting to every short-time frame;
- candidate future features include MFCC delta/delta-2 and beat-synchronous summaries.

Current boundary:

- these temporal features are **not** part of PR #140 static 78D retrieval baseline;
- #137 owns temporal-trajectory/artifact research;
- #44 owns conservative structure/change-point semantics.

---

## S5 — Librosa segmentation example: MFCC can contribute to local path similarity / structure

Type: **PRIMARY DOC**  
Source: https://librosa.org/doc/main/auto_tutorials/03-advanced/plot_segmentation.html

Relevant behavior:

- Librosa's Laplacian segmentation tutorial constructs a local sequence/path similarity from beat-synchronous MFCCs;
- successive beat distance is derived from MFCC changes and combined with recurrence information.

Genre_test use:

- supports the hypothesis that MFCC trajectories may contribute useful timbral-change evidence for #44;
- does not justify Verse/Chorus/Drop naming by itself.

Limitations:

- tutorial algorithm is an example, not a validated Genre_test structure detector;
- false-positive protection must be benchmarked on stable-tempo and hard-negative material.

---

## S6 — Reddit r/audioengineering: CLAP + MFCC similarity needs a defined target

Type: **COMMUNITY OBSERVATION**  
Source: https://www.reddit.com/r/audioengineering/comments/1rkldh7/audio_similarity_grading_question/

Context:

A user asks whether CLAP embeddings, MFCCs and envelope similarity can be combined into one timbral-similarity score. A response points out that both can be useful, but a combined metric is not meaningful without first defining the target notion of similarity.

Genre_test use:

- reinforces the project decision to keep initial outputs conceptually separate:

```text
semantic similarity
!= timbral similarity
!= structural novelty
```

- motivates benchmarking CLaMP and MFCC independently in #36 before any fusion rule.

Limitations:

- this is community advice, not a peer-reviewed result;
- no weights, thresholds or calibration values are taken from Reddit.

---

## S7 — Reddit r/DSP: MFCC-only matching can be fragile to noise/hum

Type: **COMMUNITY OBSERVATION**  
Source: https://www.reddit.com/r/DSP/comments/1j52go2

Context:

A speaker-verification hobby project based on MFCC/delta matching reportedly works in clean conditions but degrades strongly with added noise or hum.

Genre_test use:

- hypothesis: MFCC retrieval robustness must be tested under source perturbations rather than assumed;
- candidate #36 robustness fixtures should include gain changes, mild noise, codec variants and mastering variants where relevant.

Limitations:

- speech verification is not music retrieval;
- implementation quality is unknown;
- this is evidence for a robustness test, not evidence for a universal MFCC failure mode.

---

## S8 — Reddit r/MachineLearning: learned embeddings may generalize better than MFCC-style handcrafted features

Type: **COMMUNITY OBSERVATION**  
Source: https://www.reddit.com/r/MachineLearning/comments/1chmi0e

Context:

Discussion contrasts traditional MFCC/filterbank/prosodic features with learned audio embeddings. One practitioner reports better in-the-wild generalization from learned audio embeddings in their project.

Genre_test use:

- consistent with keeping CLaMP/MERT as semantic retrieval and MFCC as a comparator/complement;
- supports the non-goal: do not replace learned music embeddings with MFCC solely because MFCC is cheaper.

Limitations:

- speaker/audio tasks differ from music retrieval;
- anecdotal, not a Genre_test benchmark.

---

## S9 — GTZAN fault analysis: do not justify a new MFCC genre classifier from old headline accuracy

Type: **PRIMARY RESEARCH**  
Source: Bob L. Sturm, *The GTZAN dataset: Its contents, its faults, their effects on evaluation, and its future use*  
URL: https://arxiv.org/abs/1306.1461

Relevant findings:

- GTZAN contains repetitions, mislabelings and distortions;
- these faults affect interpretability of music-genre-recognition evaluation;
- systems evaluated on GTZAN should not be compared or trusted without accounting for dataset faults.

Genre_test use:

- rejects the simplistic direction `MFCC -> CNN/SVM -> GTZAN accuracy -> replace MAEST`;
- MAEST/AST production classification remains separate from the MFCC retrieval experiment;
- any future genre-classification change requires project-owned reviewed fixtures and modern evidence.

---

## Project-owned conclusions derived from the registry

### C1 — MFCC is complementary evidence

Current intended roles:

```text
MAEST       -> fine-style / genre evidence
AST         -> semantic evidence
CLaMP/MERT  -> semantic/multilingual retrieval
MFCC78      -> cheap timbral retrieval baseline
MFCC temporal research -> possible structure/artifact evidence (#44/#137)
```

MFCC does not replace MAEST, AST or CLaMP/MERT.

### C2 — Similarity axes stay separate until calibrated

Initial benchmark outputs should preserve distinct concepts:

- semantic similarity;
- timbral similarity;
- structural novelty/change evidence.

No production formula such as:

```text
combined = 0.8 * clamp + 0.2 * mfcc
```

is allowed without #36 project-owned relevance evidence.

### C3 — MFCC implementation identity must be explicit

The backend fingerprint/preprocessing identity should eventually cover every setting that can materially change the vector, including:

- sample rate and mono rule;
- FFT/window/hop policy;
- Mel filter count and frequency bounds;
- Mel normalization/warping behavior;
- magnitude/power/log policy;
- MFCC count;
- DCT type and normalization;
- lifter;
- chroma implementation and parameters;
- spectral-contrast implementation and parameters;
- aggregation statistics;
- input level/gain policy;
- extractor library/version or an equivalent fully pinned implementation identity.

### C4 — Gain robustness is a required benchmark concern

PR #140 review identified that MFCC coefficient 0 carries log-energy information, so otherwise identical audio at different gains can shift the 78D vector direction even after final L2 normalization.

Required follow-up before graduation:

- define a level policy or coefficient-0 policy;
- add gain-variant tests/fixtures;
- ensure #36 does not confuse loudness difference with intended timbral difference.

### C5 — Version drift is a cache/index correctness concern

If supported installations use different Librosa/NumPy/SciPy implementations but share the same backend fingerprint, vectors may be incorrectly treated as compatible.

Required follow-up:

- pin relevant extractor behavior/version, or
- include implementation identity in the backend fingerprint,
- force stale/re-embedding semantics when compatibility is not guaranteed.

---

## Benchmark hypotheses — not product claims

These expectations are intentionally recorded as hypotheses to test in #36:

| Retrieval relation | MFCC78 expected utility | CLaMP/MERT expected utility |
|---|---:|---:|
| exact / near duplicate | high | high |
| gain/mastering variant | potentially high after level policy | high |
| similar timbral balance | high | medium/high |
| instrumentation similarity | medium/high | high |
| same subgenre | low/medium | high |
| broad semantic genre | low/medium | high |
| mood / descriptive semantics | low | high |
| Russian text -> music | none | high |

These are not acceptance thresholds. #36 metrics and reviewed query labels decide whether the baseline has incremental value.

## Graduation rule

MFCC knowledge is considered integrated only when:

1. source facts remain traceable to this registry;
2. implementation parameters are versioned;
3. review findings on gain and implementation identity are resolved;
4. #36 measures real retrieval quality and robustness;
5. any future #44/#137 temporal use has independent DSP/audio-science validation;
6. unsupported community claims remain hypotheses, not product truth.
