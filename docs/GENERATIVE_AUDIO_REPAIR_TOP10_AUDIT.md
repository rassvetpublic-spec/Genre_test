# Generative Audio Repair — top-10 upstream audit

Checked: 2026-08-27  
Target workstation: Windows 11, Python 3.12, PyTorch 2.12.1+cu130, CUDA 13.0, RTX 5070 Ti 16 GB, native sm_120.  
Related: #45, #50, #52, #54, #63.

## Audit policy

Code license, model/checkpoint terms and dataset provenance are separate fields. A repository license does not automatically cover downloaded weights. “Runs on CUDA” does not prove Blackwell/cu130 compatibility. Every GPU backend therefore remains isolated and experimental until a real workstation smoke records revision, weight hash, runtime, VRAM/RAM and output checks.

Statuses:

- **SPIKE** — high priority for real compatibility/quality test;
- **BASELINE** — useful comparison implementation;
- **PROBE** — conditional research, never automatic;
- **REFERENCE** — architecture/metric source, not repair backend;
- **HOLD** — blocked by unclear terms, maintenance or fit.

## Summary matrix

| # | Project | Code terms | Weights | Runtime/system facts | Activity/maintenance | Decision |
|---:|---|---|---|---|---|---|
| 1 | [Apollo](https://github.com/JusperLee/Apollo) | README states CC BY-SA 4.0; verify LICENSE at pinned revision | Official pretrained checkpoint available; record separate checkpoint metadata/SHA-256 | Conda environment; PyTorch; CUDA/MPS/CPU selection; long-file chunk mode exists; cu130/sm_120 unverified | Checkpoints released 2024; preprocessing update 2025; repository currently accessible | **SPIKE**, highest repair relevance |
| 2 | [NVIDIA A2SB](https://github.com/NVIDIA/diffusion-audio-restoration) | NVIDIA Source Code License — Non Commercial | Model under NVIDIA OneWay NonCommercial License; pretrained initialization/checkpoints required | PyTorch Lightning stack; 44.1 kHz; long-audio bandwidth extension/inpainting; likely heavy diffusion workload | 2025 research implementation; no production package assumption | **PROBE**, research/non-commercial gate |
| 3 | [AudioSR](https://github.com/haoheliu/versatile_audio_super_resolution) | MIT repository | Basic/speech checkpoints auto-downloaded; verify checkpoint card/terms and hash separately | Upstream recommends Python 3.9; diffusion/DDIM; CUDA device option; 48 kHz output; Windows fixes documented | Latest visible changelog 2025; open issues remain | **PROBE**, separate legacy runtime |
| 4 | [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | MIT wrapper | Large catalog auto-downloaded; every UVR/MDX/MDXC/RoFormer/Demucs model requires separate identity and terms | Python package/CLI/Docker; PyTorch + ONNX Runtime; FFmpeg; CUDA 12/cuDNN 9 guidance; current Blackwell stack still needs smoke | Actively maintained with recent releases and model support | **SPIKE**, preferred separation adapter |
| 5 | [MVSEP-MDX23](https://github.com/ZFTurbo/MVSEP-MDX23-music-separation-model) | No clear repository license surfaced in checked repository page; treat as unresolved | Models downloaded on first run; includes Demucs/MDX/UVR-derived assets | GPU/CPU; >11 GB VRAM for `--large_gpu`; lower-memory modes available; standalone Windows bundle ~730 MB plus Torch/models | Contest-era project; visible issues from 2024; limited maintenance signal | **HOLD/BASELINE** until terms resolved |
| 6 | [Demucs v4](https://github.com/facebookresearch/demucs) | MIT | Pretrained model zoo downloads automatically; record exact model identity and training-data caveats | Python >=3.8; PyTorch; FFmpeg on Windows; ~7 GB typical/default VRAM, reducible by segments | Meta repo archived 2025; successor fork states minimal maintenance | **BASELINE**, not production dependency center |
| 7 | [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | MIT | Denoiser/enhancer weights obtained through package/Hugging Face; verify exact checkpoint terms/hash | 44.1 kHz speech; PyTorch/torchaudio; CUDA or CPU; enhancer uses CFM/vocoder and can be costly | Repository has open issues/PRs; package remains available | **PROBE**, vocal stem only |
| 8 | [VoiceFixer](https://github.com/haoheliu/voicefixer) | MIT | Two pretrained checkpoints: analysis `vf.ckpt` and 44.1 kHz vocoder model; verify weight terms/hash | PyTorch; CPU/CUDA; Windows requires extra wget path for old workflow; Docker image about 10 GB | Older research/package with continuing repository visibility; legacy dependency risk | **REFERENCE/PROBE**, identity-sensitive vocal test |
| 9 | [Matchering](https://github.com/sergree/matchering) | GPL-3.0 | No neural weights required | Python >=3.8, about 4 GB RAM, libsndfile; optional FFmpeg; CPU deterministic DSP | Mature project/package; active integrations, but not repair-specific | **BASELINE** for reference matching, v0.7 only |
| 10 | [Sony CSL Audio Metrics](https://github.com/SonyCSLParis/audio-metrics) | GPL-3.0 | Package itself is metric code; VGGish/CLAP embedding dependencies bring separate model terms/downloads | PyPI package; NumPy/audio embeddings; corpus/set-level evaluation rather than local repair | Recent 2025 research package | **REFERENCE** for corpus metrics |

## Detailed integration gates

### 1. Apollo

Use:

- MP3/codec-like and suspected spectral-loss fixtures;
- Safe/Probe candidate generation;
- `SOURCE_RESTORATION` analyzer robustness axis.

Before testing:

- pin Git revision;
- capture LICENSE/README terms from that revision;
- identify official checkpoint repository, filename, size, hash and terms;
- isolate runtime from Genre_test core;
- test full-file and chunked inference;
- inspect seam continuity, high-band hallucination, mono/stereo and transient preservation.

Do not claim restoration of the original signal. Transfer from MP3 training to SUNO defects remains a hypothesis.

### 2. A2SB

Use:

- bandwidth-extension comparison against Apollo;
- localized inpainting for confirmed gaps/discontinuities.

Restrictions:

- non-commercial research terms;
- diffusion cost and large dependency stack;
- require deterministic/tolerance study;
- reject candidates with invented musical events or boundary changes.

### 3. AudioSR

Use only as a boundary Probe.

Risks:

- diffusion-generated high frequencies;
- stochastic seed sensitivity;
- mono/stereo inconsistency;
- older Python/runtime recipe.

Required checks: fixed seeds, independent L/R and M/S behavior, clean-control over-processing, spectral tonality and phase stability.

### 4. python-audio-separator

Preferred adapter candidate because it supports multiple model families and current CLI/Docker flows.

Required registry fields per model:

- architecture;
- filename/checkpoint hash;
- source URL and terms;
- expected stems/sample rate;
- runtime engine: Torch or ONNX;
- VRAM/RAM and real-time factor;
- reconstruction residual and alignment.

Do not select a model from reported SDR alone.

### 5. MVSEP-MDX23

Technically useful for a 4-stem baseline, especially on the 16 GB GPU. However, absence of an explicit surfaced repository license and mixed upstream model origins block production adoption. Use only after a separate code/weight provenance resolution.

### 6. Demucs

Keep as a stable historical baseline. The archived upstream and known bleeding/artifact behavior make it unsuitable as the only active backend. Use through a maintained adapter when possible.

### 7–8. Resemble Enhance and VoiceFixer

Both are speech/vocal tools. They must receive an estimated or provided vocal stem, never the full mix by default.

Hard gates:

- pitch/formant drift;
- consonant damage;
- voice identity/timbre;
- added breath/noise;
- musical accompaniment leakage;
- final vocal-in-mix review.

### 9. Matchering

Not a v0.6 repair engine. It can provide a deterministic v0.7 reference-matching baseline, but Ozone remains the main mastering orchestration boundary. GPL implications must be reviewed before code integration.

### 10. Audio Metrics

Use for corpus/model-version comparison, not a single-track “quality score”. VGGish/CLAP model identities and terms must be recorded. Report FAD/kernel/density/coverage beside per-excerpt technical and listening results.

## Workstation compatibility order

1. python-audio-separator current Torch model on cu130/sm_120;
2. Apollo full-file and bounded-memory chunked smoke;
3. Demucs baseline through the adapter;
4. A2SB isolated research runtime;
5. AudioSR isolated legacy runtime;
6. vocal-only Resemble Enhance;
7. VoiceFixer only if Resemble/DSP baselines justify further work.

MVSEP-MDX23 remains blocked by terms clarification. Matchering and Audio Metrics are CPU/reference tools.

## Required evidence artifact per spike

```text
backend identity
code revision
code terms snapshot
checkpoint identity, size, SHA-256 and terms
Python/Torch/CUDA/cuDNN/ONNX identity
GPU name, compute capability and active architecture
input/output hash and format
load time, runtime, real-time factor
peak VRAM and RAM
cancel/unload result
repeatability delta
technical before/after delta
blind listening decision
```

## Final recommendation

Start implementation with a backend-neutral contract and two independent baselines:

- deterministic DSP/full-mix baseline;
- maintained separation adapter baseline.

Then evaluate Apollo and A2SB only on eligible defect classes. Keep all generative restorers Probe-only until clean controls, blind review and musical-damage gates pass.
