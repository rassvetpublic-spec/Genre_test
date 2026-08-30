# Open-source audio R&D references for Genre_test

Status: **external R&D references / controlled test candidates; not production truth**  
Snapshot date: **2026-08-30**

## Purpose

This document records external open-source projects that may be useful for controlled experiments around AI-audio artifacts, vocoder signatures, provenance/watermark robustness, audio-quality forensics, adversarial detector robustness, and restoration/super-resolution.

These projects are references and test candidates only. Their claims must not become `Genre_test` assumptions without independent reproduction on project-owned fixtures. Original/bypass output remains a valid winner in any repair experiment.

## Repository overview

| Repository / project | Canonical repository | Verified role / technology | Genre_test use |
|---|---|---|---|
| `geeknik/mmm` (formerly associated with `ai-audio-fingerprint-remover`) | https://github.com/geeknik/mmm | Python CLI for metadata stripping, watermark-pattern disruption, spectral perturbation, forensic analysis and lossy sanitization of MP3/WAV/FLAC. README explicitly describes AI-watermark detection classes and spectral/statistical sanitization. | **Research-only adversarial/provenance robustness fixture.** Use to test whether detectors or QC metrics are fragile under benign-looking spectral/metadata transforms. Do not treat its detector claims as ground truth and do not adopt watermark-removal as a production objective. |
| `Angel2mp3/AudioAuditor` | https://github.com/Angel2mp3/AudioAuditor | Open-source Windows/.NET audio-analysis application. README advertises fake-lossless detection, clipping/cutoff analysis, spectrogram tools and AI-generated-audio detection. | Candidate source for forensic heuristics and cross-check fixtures. Validate each heuristic independently before use. |
| `charactr-platform/vocos` → current upstream `gemelo-ai/vocos` | https://github.com/gemelo-ai/vocos | Fourier-based neural vocoder. Current configs use an `ISTFTHead`; pretrained mel and EnCodec models are available. | Reference vocoder for controlled resynthesis experiments and for studying whether Fourier-domain synthesis produces different artifact families from transposed-convolution vocoders. Do not assume that iSTFT synthesis is artifact-free. |
| `NVIDIA/BigVGAN` | https://github.com/NVIDIA/BigVGAN | PyTorch neural vocoder using Snake/SnakeBeta periodic activations and alias-free activation modules; repository references anti-aliasing filters and provides 22/24/44 kHz checkpoints. | Reference vocoder for artifact-family comparisons, aliasing tests and synthetic-control generation. Useful as a contrast to Vocos-style iSTFT reconstruction. |
| `piotrkawa/audio-deepfake-adversarial-attacks` | https://github.com/piotrkawa/audio-deepfake-adversarial-attacks | Research code for adversarial robustness of audio-deepfake detectors. README lists FGSM, FAB, PGD, PGDL2, OnePixel and CW attacks and models including RawNet3-related configurations. | Robustness-testing reference for detector evaluation. Use only in controlled experiments to quantify detector sensitivity and failure modes, not to optimize real-world evasion. |
| `facebookresearch/audioseal` | https://github.com/facebookresearch/audioseal | Meta AudioSeal: localized audio watermark generator/detector with sample-level detection and streaming support. | Positive-control watermark system for provenance experiments, localization metrics, codec/edit robustness and detector calibration. Particularly useful because the watermark generator and detector are both available. |
| `haoheliu/versatile_audio_super_resolution` (AudioSR) | https://github.com/haoheliu/versatile_audio_super_resolution | Diffusion-based versatile audio super-resolution to 48 kHz. Repository documents reconstruction limitations and sensitivity to unfamiliar cutoff patterns. | Candidate restoration/resynthesis baseline for testing whether generative super-resolution improves perceived HF quality or instead hallucinates/changes musical content. Must be judged with delta listening, loudness-matched A/B and content-retention QC. |

## Claims that require independent verification before project use

The following ideas are useful hypotheses but are **not recorded as verified Genre_test facts** merely because they appeared in external summaries:

- exact `mmm` implementation details such as a specifically named **Phase Jitter** stage, PSD-normalization formulae, or mandatory PyTorch/CuPy GPU paths;
- exact `AudioAuditor` use of **2D FFT spectral-comb detection** as a Suno/Udio-specific classifier;
- the statement that Vocos *principally excludes* all deconvolution-comb artifacts — Vocos avoids a HiFi-GAN-style waveform generator path, but this does not prove absence of periodic or spectral artifacts in generated output;
- the statement that BigVGAN simply “filters all mirrored frequencies above Nyquist” — its alias-free design is relevant, but artifact behavior must be measured rather than inferred from architecture;
- the claim that AudioSR necessarily “restores natural phase microstructure”; diffusion-based reconstruction may synthesize plausible detail, but fidelity to the original musical microstructure is an empirical question.

## Proposed controlled test families

### 1. Vocoder artifact family benchmark

Generate or resynthesize matched fixtures through Vocos and BigVGAN, then compare spectral periodicity / comb metrics, HF energy distribution and alias-like components, transient preservation, phase/coherence statistics, codec survival, and subjective loudness-matched A/B.

The goal is not to label one architecture “clean”; it is to identify which metrics distinguish artifact families without overfitting to a single generator.

### 2. Provenance and watermark robustness benchmark

Use AudioSeal as a known positive-control watermark system. Apply ordinary delivery transforms such as resampling, common codecs and gain changes, and measure detector localization/robustness.

`mmm` may be included only as a **research adversarial transform source** to test whether provenance metrics fail under spectral/metadata perturbations. Results must be framed as robustness findings, not as a production watermark-removal feature.

### 3. Detector robustness benchmark

Use ideas from `audio-deepfake-adversarial-attacks` to test whether any future Genre_test AI-audio classifier is overly sensitive to small perturbations. Keep the experiment local, fixture-based and metric-driven. Required outputs should include clean accuracy, perturbed accuracy, confidence drift, false-positive/false-negative movement and perturbation audibility.

### 4. Forensic heuristic cross-check

Treat AudioAuditor as an external heuristic reference. Reproduce only individual measurable ideas such as effective cutoff, suspicious spectral periodicity or upsampling indicators and compare them against known-source fixtures.

No heuristic may be promoted to “Suno/Udio detector” status without a documented dataset, confusion matrix and cross-generator validation.

### 5. Generative restoration / AudioSR benchmark

Compare original vs AudioSR-restored audio on deliberately bandwidth-limited or degraded fixtures. Include loudness-matched A/B, delta inspection where meaningful, spectral-distance metrics with energy normalization, transient retention, tonal/harmonic stability, mono/stereo consistency, listener preference and content-change flags.

A perceptually brighter or more detailed output is not automatically a more faithful output.

## Integration rule

External repositories in this document are **sources of hypotheses, fixtures and benchmark methods**. They are not normative dependencies. Any implementation entering `Genre_test` must be independently justified by project measurements, reproducible tests and bypass/original comparison.
