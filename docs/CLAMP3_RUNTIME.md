# CLaMP 3 Runtime Spike

Issue: **#27**  
Status: **in progress**

## Objective

Determine the safest reproducible way to run CLaMP 3 beside the released Genre_test Windows runtime.

## Current Genre_test core baseline

```text
Windows 11 x64
Python >=3.11,<3.14
PyTorch 2.12.1
CUDA 13.0 / cu130 for NVIDIA
RTX 5070 Ti / sm_120 verified
CPU-only supported
```

This baseline is already part of v0.4 release evidence and must not be destabilized merely to accommodate retrieval.

## Captured CLaMP 3 upstream baseline

Repository:

```text
https://github.com/sanderwood/clamp3
```

Candidate code snapshot:

```text
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

Upstream requirements at this snapshot:

```text
nnAudio==0.3.3
transformers==4.40.0
accelerate==0.34.0
scikit-learn==1.5.1
numpy==1.26.4
tqdm==4.66.5
unidecode==1.3.6
wandb==0.17.8
pillow==9.5.0
mido==1.3.0
samplings==0.1.7
abctoolkit==0.0.4
soundfile==0.12.1
```

Official quick-start documentation currently shows an environment around:

```text
Python 3.10.16
PyTorch CUDA 11.8
```

The upstream audio path is not raw-audio CLaMP inference. It first extracts MERT-compatible features.

## MERT preprocessing observed upstream

At the pinned CLaMP code snapshot, `preprocessing/audio/extract_mert.py` currently defines:

```text
target_sr = 24000
mono = true
normalization = false before feature extractor
sliding_window = 5 s
overlap = 0%
reduction = mean
```

The extractor then uses a `HuBERTFeature` wrapper and may mean-reduce the resulting sequence when `--mean_features` is requested.

These settings are part of embedding identity if we reproduce them.

## Candidate runtime strategies

### A. Core-native

Install all CLaMP/MERT dependencies into the existing Genre_test `.venv`.

Advantages:

- simplest process model;
- no IPC;
- potential reuse of already initialized CUDA.

Risks:

- dependency conflicts;
- old upstream packages vs released core packages;
- CLaMP research code may assume different Torch behavior;
- may destabilize MAEST/AST CUDA route;
- difficult to guarantee portable upgrades.

**Do not select without evidence.**

### B. Isolated subprocess sidecar — provisional preference

Separate environment, launched on demand by Genre_test.

```text
core .venv
    |
    +-- subprocess --> retrieval runtime
```

Advantages:

- preserves v0.4 core;
- model dependencies can be pinned independently;
- simple crash isolation;
- easy optional install/uninstall;
- CI can fake the protocol;
- sidecar can exit after indexing/search to free GPU memory.

Risks:

- startup latency;
- CUDA contexts are separate;
- VRAM may overlap if MAEST/AST remain loaded;
- IPC design required.

This is the current provisional architecture.

### C. Persistent local service

Long-running local process with a socket/HTTP transport.

Advantages:

- warm model;
- low repeated query latency.

Risks:

- lifecycle complexity;
- port/process management;
- larger security/support surface;
- unnecessary before search quality is proven.

Defer unless sidecar startup becomes a measured problem.

## Windows test matrix

At minimum test:

| Case | Core | Retrieval | Expected |
|---|---|---|---|
| GPU healthy | cu130 | official-compatible | both usable |
| GPU healthy, retrieval absent | cu130 | absent | Analyze OK, Retrieval N/A |
| GPU healthy, retrieval broken | cu130 | fail | Analyze OK, Retrieval FAIL |
| CPU-only | CPU | CPU candidate | Analyze OK, Retrieval measured |
| retrieval starts after MAEST/AST | CUDA loaded | CUDA | no OOM or explicit policy |
| retrieval first, then Analyze | CUDA | CUDA loaded | no hidden device poisoning |

## Measurements

Record on target Windows hardware:

```text
runtime install time
model download time / bytes
cold backend startup
warm backend startup
audio embedding latency
text embedding latency
peak VRAM
peak RAM
GPU utilization
sidecar shutdown time
GPU memory released after shutdown
```

For audio also record by duration:

```text
30 s
3 min
5 min
10+ min
```

## Compatibility experiments

### Experiment 1 — upstream-compatible isolated env

Goal: establish known-good reference before modernizing dependencies.

Verify:

- Python creation;
- CLaMP import;
- MERT feature extraction;
- CLaMP audio embedding;
- Russian text embedding;
- cosine self-match.

### Experiment 2 — modern Torch under isolated Python

Keep CLaMP code constant while moving only minimum runtime packages toward currently supported Torch.

Record every required patch.

If unmodified upstream works, that is evidence for future consolidation. If patches are needed, preserve them explicitly in our adapter instead of silently editing vendored research code.

### Experiment 3 — core-native import

Only after the first two experiments.

Try current Genre_test core environment without changing its pins first.

Failure is acceptable and likely means sidecar remains the correct design.

## Model loading rules

- lazy load only;
- explicit backend health before model download;
- no network fetch on module import;
- model downloads must be intentional and resumable;
- use pinned revision/checksum where available;
- cache is under Genre_test state directory or explicit configured path;
- do not bundle large third-party weights in Git or portable package.

## VRAM policy to decide

Potential policies:

1. keep MAEST/AST + CLaMP loaded concurrently;
2. unload analysis models before retrieval;
3. run CLaMP in subprocess and terminate it after indexing/search batch;
4. expose a `low-vram` retrieval mode.

Select by measurement, not assumption.

## Health model

Core-facing status:

```text
N/A  optional backend not installed/configured
OK   runtime and model ready
WARN usable but stale index / CPU fallback / degraded mode
FAIL installed/configured but not operational
```

`N/A` must not degrade global Analyze health.

## Spike completion checklist

- [ ] upstream reference env works;
- [ ] CLaMP code revision pinned;
- [ ] selected weight pinned;
- [ ] MERT source/revision pinned;
- [ ] third-party licenses recorded;
- [ ] RU text smoke passes;
- [ ] audio embedding smoke passes;
- [ ] repeatability measured;
- [ ] VRAM/RAM measured;
- [ ] core-native compatibility tested;
- [ ] final runtime architecture decision written;
- [ ] bootstrap approach drafted;
- [ ] fake backend tests green in normal CI.
