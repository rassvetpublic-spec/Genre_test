# Open-source audio R&D references for Genre_test

Status: **external R&D references / controlled test candidates; not production truth**
Snapshot date: **2026-08-30**

## Purpose

This document records external projects and services useful for controlled experiments around AI-audio artifacts, vocoder signatures, provenance/watermark robustness, audio-quality forensics, detector robustness, adversarial evaluation and restoration/super-resolution.

These projects are references and test candidates only. Their claims must not become `Genre_test` assumptions without independent reproduction on project-owned fixtures. Original/bypass output remains a valid winner in any repair experiment.

## Coverage rule — do not silently drop discovered candidates

Every detector, provenance checker, forensic analyzer, watermark implementation, adversarial-evaluation implementation or relevant signal-transform source discovered during Genre_test research must enter the research ledger, even when it is not immediately runnable.

Each discovered item must have one of these explicit states:

`DISCOVERED -> VERIFIED_SOURCE -> READY_TO_TEST -> TESTED -> RETESTED_AFTER_DEFENSE`

or an explicit blocking state such as:

`NOT_RUN_ACCESS`, `NOT_RUN_DEPENDENCY`, `NOT_RUN_DATASET`, `NOT_RUN_AUTHORIZATION_OR_TERMS`, `REJECTED_NOT_RELEVANT`, `SUPERSEDED`.

A candidate may not disappear from later summaries merely because another repository bundles a similar model. Detector architectures and attack implementations are tracked separately when they can provide distinct evidence.

## Research objective: detector robustness and defense adaptation

`Genre_test` treats detector-bypass techniques as an **adversarial research instrument for protection/process adaptation**, not as a standalone production-evasion feature.

The research objective is to measure detector/provenance robustness, identify brittle decision boundaries, reproduce controlled failures, and feed those failures into hardening, calibration and validation changes.

Preferred loop:

`baseline detector -> controlled adversarial/transform test -> characterize failure -> adapt defense/calibration -> retest clean + challenged fixtures`

Required experiment evidence includes detector version/identity, immutable source hash, transform identity, clean and challenged scores, false-positive/false-negative movement, audibility/content-change measurements, and the defensive change proposed in response.

## Open-source repository ledger

| Repository / project | Canonical repository | Verified role / technology | Genre_test status / use |
|---|---|---|---|
| `geeknik/mmm` | https://github.com/geeknik/mmm | Python CLI for metadata stripping, watermark-pattern disruption, spectral perturbation, forensic analysis and lossy sanitization. | `VERIFIED_SOURCE`; controlled provenance/watermark robustness fixture. |
| `Angel2mp3/AudioAuditor` | https://github.com/Angel2mp3/AudioAuditor | Windows/.NET audio-analysis app; fake-lossless, clipping/cutoff, spectrogram and AI-generated-audio analysis are advertised upstream. | `VERIFIED_SOURCE`; forensic-heuristic cross-check. |
| `gemelo-ai/vocos` (`charactr-platform/vocos` upstream moved) | https://github.com/gemelo-ai/vocos | Fourier/iSTFT neural vocoder. | `VERIFIED_SOURCE`; matched resynthesis and artifact-family control. |
| `NVIDIA/BigVGAN` | https://github.com/NVIDIA/BigVGAN | PyTorch vocoder with Snake/SnakeBeta and alias-free activation modules. | `VERIFIED_SOURCE`; vocoder/aliasing comparison control. |
| `piotrkawa/audio-deepfake-adversarial-attacks` | https://github.com/piotrkawa/audio-deepfake-adversarial-attacks | Defense/adversarial-evaluation research code; upstream README exposes LCNN, SpecRNet and RawNet3 configs plus FGSM, FAB, PGD, PGDL2, OnePixel and CW handling. | `VERIFIED_SOURCE`; primary controlled attack-defense benchmark source. |
| `piotrkawa/attack-agnostic-dataset` | https://github.com/piotrkawa/attack-agnostic-dataset | Upstream dependency/baseline used by the adversarial-defense repository. | `DISCOVERED`; inspect as benchmark/data/evaluation dependency rather than silently inheriting it through the parent repo. |
| `Jungjee/RawNet` / RawNet3 | https://github.com/Jungjee/RawNet | Raw-waveform speaker/audio representation implementation referenced directly by the adversarial-defense repository. | `VERIFIED_SOURCE`; detector/model-family baseline to track independently. |
| `clovaai/aasist` | https://github.com/clovaai/aasist | Official public AASIST repository for audio anti-spoofing. | `VERIFIED_SOURCE`; independent detector baseline; must be tested separately from RawNet3/SpecRNet. |
| `facebookresearch/audioseal` | https://github.com/facebookresearch/audioseal | Localized audio watermark generator/detector with sample-level detection. | `VERIFIED_SOURCE`; positive-control provenance/watermark robustness benchmark. |
| `haoheliu/versatile_audio_super_resolution` (AudioSR) | https://github.com/haoheliu/versatile_audio_super_resolution | Diffusion-based audio super-resolution to 48 kHz. | `VERIFIED_SOURCE`; restoration/resynthesis transform candidate with content-retention QC. |
| `henricksmedia/shimmer` | https://github.com/henricksmedia/shimmer | AI-audio cleanup/mastering reference with Removed/Delta audition, loudness-matched A/B and selective HF cleanup concepts. | `VERIFIED_SOURCE`; artifact-cleanup transform/control; already has dedicated `docs/SHIMMER_EXTERNAL_REFERENCE.md`. |

### Detector families explicitly not to collapse into one row

The adversarial-defense code exposes `lcnn`, `specrnet` and `rawnet3` configurations. These count as distinct detector families for the benchmark even when exercised through one repository. AASIST is also a distinct detector baseline and must not be considered covered merely because another anti-spoofing model was tested.

Minimum local detector matrix currently recorded:

- LCNN/LFCC path from `piotrkawa/audio-deepfake-adversarial-attacks`;
- SpecRNet path from that repository;
- RawNet3 path plus `Jungjee/RawNet` upstream identity;
- AASIST from `clovaai/aasist`;
- AudioAuditor AI-generated-audio heuristics;
- AudioSeal detector for watermark/provenance rather than generic human-vs-AI classification.

## External AI-music detector services already discovered elsewhere in Genre_test

A prior research branch/PR already recorded external detector services in `docs/research/EXTERNAL_AI_MUSIC_DETECTORS.md`. They were missing from the first version of this ledger and are now explicitly cross-recorded so they cannot be lost from the test backlog.

| Service | Public entry point | Ledger state |
|---|---|---|
| authio / Forward Digital AI Music Checker | https://authio.io/ai-music-checker | `DISCOVERED`; external comparison candidate. |
| ACRCloud AI Music Detector | https://acrcloud.com/ai-music-detector/ | `DISCOVERED`; external comparison/API candidate. |
| IRCAM Amplify AIMD | https://www.ircamamplify.com/ | `DISCOVERED`; access-dependent external validation candidate. |
| Pex / Vobile AI Song Detector | https://pex.com/ai-song-detector/ | `DISCOVERED`; enterprise/demo/API external validation candidate. |
| Detector24 AI Music Detection | https://detector24.ai/products/ai-music-detection | `DISCOVERED`; account/API external score comparison. |
| PesneGen | https://pesnegen.ru/analiz-treka-online | `DISCOVERED`; public-upload external analysis candidate. |

External-service runs remain subject to the disclosure/authorization/terms gate recorded in the dedicated detector reference. If a fixture cannot legally or appropriately be uploaded, record `NOT_RUN_AUTHORIZATION_OR_TERMS` rather than omitting the service.

## Claims requiring independent verification

The following remain hypotheses until reproduced from upstream code/tests or Genre_test fixtures:

- exact `mmm` implementation details such as a specifically named Phase Jitter stage, PSD-normalization formulae, or mandatory PyTorch/CuPy GPU paths;
- exact AudioAuditor use of 2D-FFT spectral-comb detection as a Suno/Udio-specific classifier;
- any claim that Vocos is artifact-free because it uses iSTFT;
- any claim that BigVGAN's alias-free architecture guarantees absence of mirrored/periodic artifacts;
- any claim that AudioSR faithfully restores original phase/HF microstructure rather than synthesizing plausible detail.

## Mandatory benchmark families

### Detector baseline benchmark

Run each locally available detector family independently on the same immutable clean control set. Record ROC/AUC where meaningful, thresholded confusion matrix, calibration/confidence distributions, generator/source-family breakdown and codec/mastering robustness.

### Controlled attack-defense benchmark

For locally controlled models, use the adversarial-defense research implementation to evaluate supported challenge methods and transferability under bounded experimental conditions. Results are durability findings: successful challenge cases must trigger a hardening/recalibration hypothesis and clean+challenged retest.

### Provenance/watermark benchmark

Use AudioSeal as a known positive control. Exercise normal delivery transforms and controlled robustness challenges, measuring localization, detection confidence, false positives and survival.

### Forensic-heuristic benchmark

Exercise AudioAuditor-derived measurable features separately from learned classifiers. Do not label a heuristic a Suno/Udio detector without controlled dataset evidence and cross-generator validation.

### Vocoder/artifact benchmark

Compare matched Vocos/BigVGAN fixtures and native generator fixtures using spectral periodicity, HF energy, alias-like components, phase/coherence, transient retention, codec survival and loudness-matched listening.

### Cleanup/restoration transform benchmark

Include Shimmer-style cleanup and AudioSR as transformation candidates. Judge them by content retention, delta/Removed audition where applicable, transient safety, loudness-matched A/B and whether detector/provenance evidence changes as a side effect.

## Integration rule

External repositories and services are **sources of hypotheses, fixtures, baselines and benchmark methods**, not normative truth. Any implementation entering Genre_test must be justified by reproducible project measurements.

The research ledger is append-only in spirit: new candidates may be rejected, blocked or superseded, but they should not be silently forgotten. A research summary claiming broad detector/robustness coverage must reconcile itself against this ledger first.
