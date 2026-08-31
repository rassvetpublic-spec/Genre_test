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

Community material may motivate a test, but only project-owned benchmark evidence may justify calibration, score fusion, production ranking, or semantic claims.

## Evidence classes

- **PRIMARY DOC** — official library/API documentation.
- **PRIMARY RESEARCH** — research paper or equivalent primary publication.
- **UPSTREAM CODE** — inspectable third-party implementation pattern.
- **COMMUNITY OBSERVATION** — hypothesis-generating only.
- **PROJECT DECISION** — Genre_test engineering decision derived from evidence and current architecture.

## S1 — `horacio/simil`: model-free music-similarity baseline

Type: **UPSTREAM CODE**
Repository: `https://github.com/horacio/simil`
Inspected revision: `cb6da9ccd5ea6c675b66ad8d3b378f0a6ca322de`
Pinned file: `simil/embedders/mfcc.py`

Relevant behavior verified at the pinned revision:

- MFCC + chroma + spectral-contrast embedder;
- 20 MFCC coefficients, 12 chroma bins and 7 spectral-contrast values;
- mean + standard deviation aggregation to 78 dimensions;
- 22.05 kHz mono input and final L2 normalization;
- learned and handcrafted spaces remain separate.

Genre_test use:

- motivates a cheap independent handcrafted acoustic comparator;
- motivates the initial `20 + 12 + 7 -> mean/std -> 78D` shape;
- does not prove those parameters or their relative weighting are optimal;
- Genre_test does not copy the upstream clip-selection or implicit weighting policy.

## S2 — Librosa MFCC API

Type: **PRIMARY DOC**
Source: `https://librosa.org/doc/main/api/generated/librosa.feature.mfcc.html`

Relevant facts:

- MFCC output depends on coefficient count, DCT type/normalization, liftering and Mel-spectrogram configuration;
- multi-channel behavior can differ from independent channel calculation.

Genre_test use:

- the feature extractor is intentionally mono;
- MFCC parameters and extractor implementation identity belong in the backend fingerprint.

## S3 — Essentia MFCC reference

Type: **PRIMARY DOC**
Source: `https://essentia.upf.edu/reference/streaming_MFCC.html`

Essentia exposes materially different MFCC choices including Mel-band count/frequency bounds, coefficient count, DCT type, liftering, log-compression policy, spectrum policy, filter normalization and sample rate.

Genre_test use:

- there is no safe identity `backend=mfcc` without preprocessing details;
- incompatible extractor implementations must never silently share one cache/index identity;
- Essentia and Librosa vectors are not assumed numerically interchangeable.

## S4 — Librosa MFCC temporal examples

Type: **PRIMARY DOC**
Source: `https://librosa.org/doc/0.10.2/tutorial.html`

MFCC deltas and beat-synchronous aggregation motivate future temporal research under #44/#137. These features are not part of static ACOUSTIC78 and are not interpreted as AI-origin truth.

## S5 — Librosa segmentation example

Type: **PRIMARY DOC**
Source: `https://librosa.org/doc/main/auto_tutorials/03-advanced/plot_segmentation.html`

Beat-synchronous MFCC change can contribute to conservative acoustic change-point evidence. It does not justify Verse/Chorus/Bridge/Drop naming.

## S6 — community observation: CLAP + MFCC fusion needs a defined target

Type: **COMMUNITY OBSERVATION**

Useful hypothesis: handcrafted and learned embeddings can both help, but a combined score is meaningless until the target notion of similarity is defined.

Genre_test interpretation:

```text
semantic similarity
!= handcrafted acoustic similarity
!= structural novelty
```

Benchmark CLaMP/MERT and ACOUSTIC78 independently in #36 before any score fusion. No community weights or thresholds are adopted.

## S7 — robustness under noise/hum

Type: **COMMUNITY OBSERVATION**

Useful only as motivation to measure robustness. #36 fixtures should include gain changes, mild noise, codec variants and mastering variants where relevant.

## S8 — learned embeddings versus handcrafted audio features

Type: **COMMUNITY OBSERVATION**

Supports keeping CLaMP/MERT as the learned semantic retrieval path while ACOUSTIC78 remains a comparator/complement, not a replacement.

## S9 — GTZAN fault analysis

Type: **PRIMARY RESEARCH**
Source: Bob L. Sturm, *The GTZAN dataset: Its contents, its faults, their effects on evaluation, and its future use*
URL: `https://arxiv.org/abs/1306.1461`

Genre_test interpretation:

- reject shortcuts from old MFCC/GTZAN headline accuracy to production classifier replacement;
- MAEST/AST production classification stays separate from handcrafted retrieval research.

## Project-owned conclusions

### C1 — ACOUSTIC78 is complementary acoustic evidence

```text
MAEST       -> fine-style / genre evidence
AST         -> semantic evidence
CLaMP/MERT  -> semantic / multilingual retrieval
ACOUSTIC78  -> cheap handcrafted acoustic baseline
```

Because the 78D representation contains chroma, it is **not a timbre-only axis**. Chroma contributes pitch-class/harmonic information and can respond to key/harmony/transposition. The backend therefore uses `mfcc-acoustic78` / handcrafted acoustic terminology.

### C2 — similarity axes stay separate until calibrated

No production fusion formula is allowed without #36 project-owned relevance evidence.

### C3 — implementation identity is part of vector compatibility

The V3 fingerprint records:

- SoundFile/libsndfile float32 decode;
- explicit channel mean;
- explicit SciPy `resample_poly` to 22.05 kHz;
- SoundFile/libsndfile runtime versions;
- strict 22.05 kHz feature-extraction rate;
- FFT/hop and feature counts;
- fixed RMS analysis-level policy;
- minimum usable input RMS (`-80 dBFS`);
- mean/std aggregation policy;
- equal feature-family norm weighting before final L2;
- Librosa, NumPy and SciPy versions;
- baseline algorithm revision.

The backend deliberately does not silently fall back to another decoder under the same fingerprint. Unsupported files fail this optional benchmark independently.

### C4 — global-gain dependence is controlled

MFCC coefficient 0 carries log-energy information, so pure global gain can rotate raw MFCC statistics. V3 rejects unusable near-silence, normalizes valid input to RMS `0.1`, retains all 20 MFCC coefficients and tests gain variants.

### C5 — runtime/preprocessing drift is controlled

Decoder/resampler/extractor runtime identity and preprocessing policy contribute to `preprocessing_version`, which contributes to `RetrievalBackendInfo.fingerprint`. Incompatible vectors therefore require re-embedding.

### C6 — feature-family scale is explicit

```text
MFCC mean/std block      -> block L2
chroma mean/std block    -> block L2
contrast mean/std block  -> block L2
three equal-norm blocks  -> concatenate -> final L2
```

Equal family norm is a declared benchmark policy, not a claim that equal weighting is optimal. The shared backend-info `normalization` field remains `l2`; family equalization is fingerprinted preprocessing semantics.

### C7 — practical near-silence is rejected before amplification

V3 rejects inputs below `-80 dBFS RMS` before scaling to the target analysis level. The threshold is part of the fingerprint and remains benchmark policy subject to #36 corpus validation.

## Benchmark hypotheses — not product claims

| Retrieval relation | ACOUSTIC78 expected utility | CLaMP/MERT expected utility |
|---|---:|---:|
| exact / near duplicate | high | high |
| gain variant | high after V3 level normalization | high |
| mastering / codec variant | benchmark required | benchmark required |
| similar timbral balance | high | medium/high |
| same key/harmony | can influence score via chroma | semantic relevance varies |
| instrumentation similarity | medium/high | high |
| same subgenre | low/medium | high |
| mood / descriptive semantics | low | high |
| Russian text -> music | none | high |

These are hypotheses, not acceptance thresholds.

## Graduation rule

The handcrafted baseline may graduate from benchmark utility only when:

1. source facts remain traceable to pinned sources where implementation details are derived;
2. decode/resample, feature preprocessing, weighting and extractor runtime identity are versioned;
3. gain, near-silence, sample-rate, decode/resample and family-weighting findings remain covered by tests;
4. #36 measures real retrieval quality and perturbation robustness;
5. future temporal use receives independent DSP/audio-science validation;
6. unsupported community claims remain hypotheses, not product truth.

`BYPASS` / no-use is a valid final outcome if #36 shows no incremental value.
