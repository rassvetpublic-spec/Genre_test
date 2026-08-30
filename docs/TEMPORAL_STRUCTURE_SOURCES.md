# TemporalStructureProfile research source registry

Status: pinned research registry  
Snapshot date: 2026-08-30  
Issue: #137  
Related: #45, #50, #54, #63, `TEMPORAL_STRUCTURE_PROFILE.md`

## Purpose

This registry records external literature and reproducible code that may inform `TemporalStructureProfileV1`, corpus design, calibration, and repair validation.

External claims are **not** project ground truth. A paper or detector result may motivate a metric, control group, or robustness test, but no external result may be converted into a universal `AI`, `HUMAN`, `SUNO`, generator-attribution, or repair threshold without Genre_test-owned benchmark evidence.

For every source, distinguish:

1. what the source actually supports;
2. what it does **not** establish for Genre_test;
3. which project experiment it motivates;
4. whether code/data are reproducible and which revision was inspected.

## Primary sources

### S1 — Afchar et al., 2025 — Fourier artifacts

**Paper:** Darius Afchar, Gabriel Meseguer-Brocal, Kamil Akesbi, Romain Hennequin. *A Fourier Explanation of AI-music Artifacts*. ISMIR 2025, pp. 739–746.  
ArXiv: https://arxiv.org/abs/2506.19108  
ISMIR proceedings: https://ismir.net/conferences/ismir-2025/  
Official code: https://github.com/deezer/ismir25-ai-music-detector  
Pinned code snapshot inspected: `dc8713a24bc3a593ac44fef96897cdde67e93d26`.

**Supports:**

- some generative decoder/deconvolution architectures can produce systematic frequency-domain artifacts;
- the reported phenomenon appears as small, structured spectral peaks related to architectural upsampling/deconvolution behaviour;
- the authors validate the phenomenon on open models and report experiments involving commercial generators including Suno and Udio;
- an interpretable spectral criterion can be competitive with learned detectors in the paper's evaluated scenarios.

**Does not establish:**

- that every generated song exposes the same peak pattern;
- that every periodic spectral peak is generative evidence;
- that Genre_test's current `periodic_peak_score` reproduces the paper's detector;
- that a spectral-peak anomaly is an audible defect or should be repaired.

**Genre_test action:**

- keep `spectral_artifacts` explicitly exploratory;
- benchmark periodic peak spacing/persistence across generators, human hard negatives, mastering and codec variants;
- compare the current lightweight extractor against the pinned reference implementation before claiming method equivalence.

---

### S2 — Afchar, Meseguer-Brocal & Hennequin, 2025 — detector robustness caveats

**Paper:** *AI-Generated Music Detection and its Challenges*. ICASSP 2025.  
ArXiv: https://arxiv.org/abs/2501.10111  
Official code: https://github.com/deezer/deepfake-detector  
Pinned code snapshot inspected: `edc94ad04b721e4ba59ccfb25e14606ddaa4a78a`.

**Supports:**

- high in-dataset detector accuracy does not settle deployment reliability;
- robustness to audio manipulation and generalization to unseen generators are first-class validation problems;
- matched-content/reconstruction experiments can reduce confounding between musical content and synthetic artifacts.

**Does not establish:**

- that a detector trained on one reconstruction/generator family generalizes to all future models;
- that any one Genre_test metric should become a binary origin classifier.

**Genre_test action:**

- require generator-held-out and processing-held-out tests;
- report hard-negative false positives separately from aggregate accuracy;
- never promote an interpretive threshold from a single corpus split.

---

### S3 — Rahman et al., 2024/ICLR 2025 — SONICS

**Paper:** Md Awsafur Rahman, Zaber Ibn Abdul Hakim, Najibul Haque Sarker, Bishmoy Paul, Shaikh Anowarul Fattah. *SONICS: Synthetic Or Not — Identifying Counterfeit Songs*.  
ArXiv: https://arxiv.org/abs/2408.14080  
Project: https://awsaf49.github.io/sonics-website/  
Official code: https://github.com/awsaf49/sonics  
Pinned code snapshot inspected: `9156ffad151f797c71556923c4a02fa01fa8fc91`.

**Supports:**

- end-to-end synthetic-song detection needs full-song datasets rather than only singing-voice deepfake sets;
- SONICS contains more than 97k songs / 4,751 hours, with more than 49k synthetic songs including Suno and Udio material;
- long-range temporal dependencies are useful in the authors' evaluation and motivate looking beyond short local spectra.

**Does not establish:**

- that Genre_test should copy SONICS labels or thresholds;
- that short-time MFCC/rhythm/transient statistics alone capture the long-range signal used by SpecTTTra;
- that SONICS class balance reflects real-world prevalence.

**Genre_test action:**

- preserve source/song family groups across splits;
- include long-range/segment-distribution analysis in addition to local metrics;
- use SONICS as an external comparison reference where dataset terms permit, not as a substitute for project-owned hard negatives.

---

### S4 — Morosanu et al., 2026 — edited audio as hard negative

**Paper:** Alexandru-Stefan Morosanu, Valerian Cecan, Stefan-Daniel Achirei, Laura Erhan. *Distinguishing AI-Generated Music from Edited Audio as a Hard-Negative Robustness Task*.  
ArXiv: https://arxiv.org/abs/2608.14916

**Supports:**

- edited/re-encoded/pitch-shifted audio can overlap with spectral cues used for synthetic-music detection;
- the authors report lower performance on edited negatives than on generated positives in their test setup;
- anchor-song grouping is important to reduce train/test leakage.

**Does not establish:**

- that all edits mimic generative artifacts equally;
- that the paper's PaSST decisions identify the same evidence as `TemporalStructureProfileV1`;
- that an edited track with an anomalous metric is generated.

**Genre_test action:**

- make edited human audio a mandatory hard-negative family;
- group variants by immutable parent/anchor source before splitting;
- include codec, limiter/mastering, pitch/time edits and stem recombination as processing axes.

---

### S5 — Afchar & Hennequin, 2026 — zero-shot artifact evidence

**Paper:** Darius Afchar, Romain Hennequin. *Finding the noise: Zero-shot AI Music Detection*.  
ArXiv: https://arxiv.org/abs/2607.25530

**Supports:**

- unknown/new generator families motivate one-class, zero-shot, clustering and artifact-extraction approaches rather than only closed-set supervised classification;
- interpretable artifact extraction can be combined with simple decomposition/classification methods for generator-unknown settings.

**Does not establish:**

- that zero-shot clustering is equivalent to provenance attribution;
- that an outlier from a human-reference distribution is automatically generated;
- that Genre_test should expose a zero-shot origin score in ordinary Analyze.

**Genre_test action:**

- keep distribution/outlier analysis research-only;
- test generator-held-out generalization;
- store feature vectors and distributions before considering any classifier layer.

---

### S6 — Lopez-Ayala et al., 2026 — duration and masking robustness

**Paper:** David Lopez-Ayala, Asier Cabello, Pablo Zinemanas, Emilio Molina, Martin Rocamora. *AI-Generated Music Detection in Broadcast Monitoring*.  
ArXiv: https://arxiv.org/abs/2602.06823

**Supports:**

- performance measured on clean/full music can degrade severely for short excerpts and speech-masked/background music;
- evaluation should explicitly vary duration and foreground/background conditions;
- AI-OpenBMAT provides a broadcast-oriented example with 3,294 one-minute excerpts / 54.9 hours.

**Does not establish:**

- that Genre_test needs a broadcast detector;
- that short-window metric instability is generator evidence.

**Genre_test action:**

- include excerpt-duration sensitivity in distribution reports;
- record insufficient-duration/insufficient-onset states rather than forcing a score;
- avoid calibrating on one fixed segment duration only.

---

### S7 — Sharma & Wang, ACL 2026 — MFCC as one complementary view

**Paper:** Aastha Sharma, Guangjing Wang. *A Unified Feature Mixture Framework for Joint Speech and Singing Deepfake Detection*. Findings of ACL 2026, pp. 24853–24863.  
ACL Anthology: https://aclanthology.org/2026.findings-acl.1245/  
DOI: https://doi.org/10.18653/v1/2026.findings-acl.1245  
Official code: https://github.com/aastha-sharma/genuvoice  
Pinned code snapshot inspected: `f75995f064ddcd33637d6fec0aa17f50f79520cd`.

**Supports:**

- MFCC can contribute as one complementary feature view in a multi-expert detector alongside Wav2Vec 2.0 and log-mel features;
- feature fusion can outperform relying on a single representation in the authors' speech/singing deepfake domain.

**Does not establish:**

- that MFCC alone detects generated music;
- that speech/singing voice deepfake results transfer directly to full-mix end-to-end music generation;
- that smooth MFCC trajectories are a universal synthetic signature.

**Genre_test action:**

- retain MFCC temporal metrics as descriptive features, not provenance truth;
- compare them jointly with onset/transient/spectral evidence only after corpus calibration;
- keep full-mix music evaluation separate from voice-deepfake literature.

## Source hierarchy

When sources disagree or scope differs, use this order for project decisions:

1. Genre_test-owned locked test/challenge evidence;
2. reproducible paper + pinned official implementation on a comparable task;
3. peer-reviewed/arXiv paper without reproduced code;
4. external detector output with disclosed methodology;
5. undocumented commercial detector output, screenshots, forum claims, model chat, anecdote.

Levels 4–5 may create a hypothesis but cannot set a project threshold.

## Reproducibility record

When an external method is actually executed in Genre_test, add a run record with:

```text
source_id
paper_version / DOI / arXiv version
repository_url
commit_sha
model/checkpoint identity + SHA-256 when applicable
dataset/split identity
runtime/dependency identity
input asset hashes
configuration hash
output artifact hashes
notes on deviations from paper/code
```

A moving `main`/`latest` reference is insufficient for a benchmark result.

## Current project conclusion

The literature supports a **multi-axis, robustness-first research program**, not a magic AI detector. For `TemporalStructureProfileV1`, the actionable scientific questions are:

- whether MFCC temporal dynamics differ after controlling for genre, source family and processing;
- whether microtiming/transient statistics add independent evidence beyond hard-quantized human music;
- whether periodic spectral structure remains discriminative after mastering/codec/editing;
- whether local evidence is stable across excerpt duration and long-range song context;
- whether any evidence corresponds to an audible repairable defect rather than merely provenance-correlated structure.

The next required stage is the project-owned corpus/distribution/calibration/repair-validation pipeline defined in `TEMPORAL_STRUCTURE_RESEARCH_PIPELINE.md`.
