# AI Origin & Provenance Lab

Status: **accepted architecture plan / not yet production implementation**  
Epic: **#80**  
Target: local-first `Genre_test` subsystem for AI-origin detection and generator-family attribution.  
Primary workstation: **RTX 5070 Ti 16 GB, Blackwell sm_120, PyTorch 2.12.1+cu130, CUDA 13.0**.

## 1. Scope

This subsystem answers a different question from the existing analyzers:

- `AudioProfile` — what the music sounds like / genre and semantic profile;
- `GenerativeDefectProfile` — what audible defects are present and whether repair is justified;
- `TechnicalProfile` — measurable technical state;
- `OriginProfile` — what forensic/model evidence supports human or AI origin and, when justified, which generator family is most likely.

AI-origin evidence must never be used as a mastering/repair optimization target. The project does not implement detector evasion, watermark removal, provenance stripping or concealment.

## 2. Target output: OriginProfileV1

Required verdicts:

```text
HUMAN_LIKELY
AI_LIKELY
MIXED_OR_PARTIAL
UNCERTAIN
INSUFFICIENT_EVIDENCE
```

Required source-family vocabulary:

```text
HUMAN
SUNO
UDIO
MUSICGEN
STABLE_AUDIO
AUDIOLDM
RIFFUSION
OTHER_AI
UNKNOWN
```

Hard truth rule: absence of a known AI fingerprint is **not** proof of human origin.

Each result must retain:

- calibrated origin score/probability semantics;
- confidence/uncertainty state;
- per-stream evidence;
- timestamped segment evidence where applicable;
- source-family evidence only when supported;
- detector/model/calibration revisions;
- input/source identity;
- robustness evidence where evaluated.

## 3. Multi-stream detector architecture

```text
                         ORIGINAL AUDIO
                              |
              +---------------+----------------+
              |                                |
       forensic/native                  semantic/structure
       44.1/48 kHz                            24 kHz
              |                                |
     +--------+---------+            +---------+----------+
     |        |         |            |         |          |
  Fourier   CQT/     codec/       MERT      Long      Human
 fakeprint  CNN      residual     95M     Context     Novelty
     |        |         |            |    sequence        |
     +--------+---------+            +---------+----------+
              |                                |
              +---------------+----------------+
                              |
                    SOURCE ATTRIBUTION
               Suno / Udio / MusicGen /
              Stable Audio / AudioLDM /
                Riffusion / Other AI
                              |
                     calibrated fusion
                              |
                   conformal uncertainty
                              |
                       OriginProfileV1
```

The streams intentionally target different failure modes. Production fusion is evidence-calibrated; no simple majority vote is allowed.

## 4. Stream A — Fourier / decoder fakeprint

Purpose: inexpensive physical-forensic evidence from regular spectral residuals associated with neural decoder/vocoder families.

Implementation direction:

- long FFT/STFT average spectrum;
- lower spectral-envelope subtraction;
- residual peak/fakeprint vector;
- configurable forensic frequency band;
- interpretable peak/residual evidence;
- lightweight calibrated baseline classifier.

This stream should run CPU-only and establish the first benchmark floor.

Critical rule: do not derive this evidence only from the existing 16 kHz MAEST analysis stream. Preserve a native/high-rate forensic view.

## 5. Stream B — CQT forensic CNN

Purpose: learn complementary local forensic patterns while improving robustness to ordinary delivery and mastering transformations.

Primary candidate:

```text
audio -> CQT/log-frequency representation -> compact CNN -> forensic score
```

Mandatory train/benchmark augmentation matrix:

- MP3 at multiple bitrates, including aggressive streaming-like conditions;
- AAC at multiple bitrates/profiles where reproducibly supported;
- Opus at multiple bitrates;
- 44.1/48 kHz resampling and selected lower-rate stress cases;
- ordinary EQ;
- compression;
- limiting and loudness normalization;
- controlled noise;
- phase rotation / phase shifts;
- plausible stereo channel-phase perturbations.

The benchmark must separately measure:

1. AI evidence masked by lossy compression;
2. codec artifacts causing false AI positives on human material;
3. phase processing causing verdict instability;
4. accidental bitrate/codec classification instead of origin classification.

Target stream VRAM: `< 1.5 GB` unless locked benchmark evidence proves a larger model is necessary.

## 6. Stream C — Verified Human novelty / OOD

Purpose: detect unfamiliar synthetic generators without requiring examples from every generator family.

Preferred direction: reuse existing pinned MERT embeddings and model the distribution of **verified human** music using lightweight candidates first:

- Mahalanobis/covariance baselines;
- kNN/local-density novelty;
- one-class SVM where practical;
- compact normalizing flow if it proves materially better.

### Verified Human purity

The human reference set must not be treated as a single homogeneous distribution. Mahalanobis/flow models are especially sensitive to remasters, old digitizations and unusual mastering chains.

Required human strata where available:

- modern native/lossless masters;
- modern remasters;
- legacy masters / old digitizations;
- lossy-source human tracks;
- live/acoustic material;
- electronic/heavily processed human material;
- genre-balanced subsets;
- artist-disjoint calibration/test subsets.

`VERIFIED_HUMAN` requires provenance evidence. Unknown catalog tracks must not silently enter one-class training or calibration.

Required reporting includes per-stratum and per-genre FPR, not only aggregate FPR.

OOD evidence alone does not mean `AI`; it is one evidence stream for calibrated fusion.

## 7. Stream D — MERT long-context detector

Reuse the already validated `MERT-v1-95M` runtime from #29. Do not add another heavyweight MERT stack unless measured evidence requires it.

### Segment policy

Accepted default benchmark candidate:

```text
window = 5.0 s
stride = 2.5 s
```

The 50% overlap is intentional: strict 5-second non-overlapping windows can miss synthetic splice/transition boundaries.

Required ablation:

```text
5.0 s window / 2.5 s stride
vs
5.0 s window / 5.0 s stride
```

The project must measure the value and runtime cost rather than assume it.

Important leakage rule: overlapping segments from the same song must never cross train/test/calibration partitions.

### Shared embedding cache

Cache identity must include:

- source hash/track identity;
- MERT model revision;
- preprocessing revision;
- window length;
- stride;
- normalization/embedding identity.

When compatible, one MERT segment sequence should be reusable by retrieval, long-context origin analysis, human novelty and attribution.

Sequence-head candidate: compact Transformer (roughly 4–6 layers) or a simpler measured alternative if it performs as well.

## 8. Stream E — hierarchical generator attribution

Origin verdict and generator attribution are separate decisions.

```text
ORIGIN
|- HUMAN
|- AI
|  |- SUNO
|  |- UDIO
|  |- MUSICGEN
|  |- STABLE_AUDIO
|  |- AUDIOLDM
|  |- RIFFUSION
|  `- OTHER_AI
`- UNKNOWN
```

Rules:

- never force an unsupported generator into Suno/Udio because it has the largest weak score;
- `OTHER_AI` and `UNKNOWN` are first-class states;
- attribution cannot override stronger origin uncertainty;
- generator family/version metadata must be explicit in benchmark manifests.

Use lightweight classifiers over MERT/long-context/forensic evidence first. More complex heads require benchmark justification.

## 9. Stream F — optional provenance evidence

Potential inputs:

- container/file metadata;
- supported Content Credentials/C2PA evidence;
- known supported provenance markers/watermarks where legitimately detectable.

Positive provenance evidence may be strong. Absence of such markers provides no proof of human origin.

## 10. Calibrated fusion

Forbidden:

```text
three detectors vote AI, two vote Human -> AI
```

Preferred candidates:

- logistic meta-classifier;
- monotonic gradient boosting where useful;
- isotonic/Platt calibration;
- split-conformal thresholds on a disjoint verified-human calibration set.

Potential inputs:

- Fourier fakeprint score;
- CQT forensic score;
- codec/residual/phase evidence;
- verified-human novelty score;
- long-context score;
- attribution evidence;
- optional provenance evidence.

MAEST genre/family may select or inform a validated calibration regime but must not silently become AI-origin evidence.

A stream enters production fusion only if it improves the locked benchmark, especially worst-generator Recall@1%FPR, or materially reduces human false positives/uncertainty without unacceptable regressions.

## 11. Benchmark contract

### Primary metric

**Worst-generator Recall @ 1% verified-human FPR**.

### Additional metrics

- Recall @ 0.1% FPR;
- Recall @ 5% FPR;
- ROC-AUC;
- PR-AUC;
- Brier score;
- expected calibration error or equivalent calibration diagnostic;
- per-generator performance;
- worst-generator performance;
- per-genre human FPR;
- per-human-stratum FPR;
- score drift and verdict-flip rates under transformations.

### Primary generalization protocol

**LOGO — Leave One Generator Out.**

For each fold, one entire generator family is excluded from training and tested as unseen.

Human data must remain artist/song-disjoint. Alternate encodes, remasters, covers and duplicate source songs must not cross partitions.

### Content-matched controls

Where possible, use content-matched pairs to prevent the detector learning dataset, era, genre or mastering source rather than origin.

### External holdouts

External benchmark families/corpora must remain untouched until final evaluation for the corresponding experiment.

## 12. Robustness Lab

For benchmark sources, create tracked derived variants such as:

```text
native WAV/lossless
MP3 multiple bitrates
AAC multiple bitrates
Opus multiple bitrates
44.1 <-> 48 kHz resampling
loudness normalization
ordinary EQ
compression
limiting/mastering
phase rotations / controlled channel-phase variants
```

Derived variants must retain source-parent lineage and never replace source truth.

Origin robustness is a separate metric namespace and must not be confused with existing analyzer-build `DRIFT` or repair `SOURCE_RESTORATION`.

## 13. Runtime architecture for RTX 5070 Ti 16 GB

The project should not keep all heavy models resident simultaneously.

Recommended flow:

```text
CPU fakeprint
 -> compact CQT CNN
 -> release if appropriate
 -> MERT segment embedding extraction
 -> reuse cached embeddings
 -> lightweight long-context / novelty / attribution heads
 -> CPU/lightweight calibrated fusion
```

Current project evidence from #29 already confirms the existing MERT/CLaMP backend runs on the target Blackwell GPU with approximately 2.25 GB allocated and 2.44 GB peak CUDA memory in the measured smoke.

Origin runtime gates:

```text
normal target peak VRAM < 8 GB
hard promotion gate      < 11 GB
```

Preserve headroom for the wider SUPERCOMBINE workflow.

Required runtime behavior:

- no hidden model downloads;
- versioned model identities;
- deterministic stage ownership;
- structured missing-backend/OOM failures;
- clean model release;
- origin backend failure must not make ordinary Analyze unusable;
- CPU-only semantics explicit where supported.

## 14. Work packages

- #81 — `OriginProfileV1` schema, truth semantics, benchmark protocol;
- #82 — native forensic decode views + Fourier fakeprint baseline;
- #83 — CQT forensic CNN with codec/bitrate/phase robustness;
- #84 — shared MERT segment cache + overlapping long-context detector;
- #85 — verified-human novelty/OOD detector with remaster/digitization controls;
- #86 — hierarchical generator-family attribution;
- #87 — calibrated multi-stream fusion + conformal uncertainty;
- #88 — local runtime, CLI/GUI/history integration and RTX 5070 Ti gates.

## 15. Implementation order

```text
P0
#81 schema + benchmark truth
#82 native forensic path + fakeprint

P1
#83 CQT robustness stream
#84 shared MERT + long context

P2
#85 verified-human novelty
#86 source attribution
#87 calibrated fusion

P3
#88 product/runtime integration
```

Do not begin by wiring many third-party detector stacks together. Reuse ideas and independently reproduce useful methods around the already proven Genre_test runtime.

## 16. Merge rule

All AI Origin & Provenance Lab work follows the project rule:

**no merge without explicit MTD.**
