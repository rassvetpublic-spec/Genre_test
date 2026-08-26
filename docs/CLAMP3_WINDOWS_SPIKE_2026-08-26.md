# CLaMP 3 Windows spike evidence — 2026-08-26

Issue: #27

Source: local read-only `scripts/clamp3_windows_inventory.ps1` run on the target Genre_test workstation.

## Host

```text
Computer: RASSVET_DESKTOP
OS: Microsoft Windows 11 Pro Insider Preview
Version: 10.0.26220
Build: 26220
```

## Available Python interpreters

```text
Python 3.13: available
Python 3.12: available
Python 3.11: not registered
Python 3.10: not registered
```

Core Genre_test currently runs:

```text
Python 3.12.10
C:\GIT\Genre_test\.venv\Scripts\python.exe
```

## GPU

```text
NVIDIA GeForce RTX 5070 Ti
Driver: 610.88
VRAM: 16303 MiB
Compute capability: 12.0
```

## Core PyTorch/CUDA evidence

```text
PyTorch: 2.12.1+cu130
CUDA available: true
Torch CUDA: 13.0
GPU: NVIDIA GeForce RTX 5070 Ti
Capability: (12, 0)
Compiled architectures:
  sm_75
  sm_80
  sm_86
  sm_90
  sm_100
  sm_120
```

This confirms the released core route is Blackwell-native on this workstation.

## Commands available

```text
git: yes
py: yes
python: yes
nvidia-smi: yes
ffmpeg: yes
```

## Runtime decision impact

The machine does **not** currently provide Python 3.10, while the upstream CLaMP research quick-start documents an older Python/CUDA environment. More importantly, the target GPU is Blackwell `sm_120`, so the production retrieval route must preserve a modern CUDA/PyTorch path capable of native Blackwell execution.

Therefore the spike order is now:

1. **isolated modern sidecar first** — Python 3.12 + current Blackwell-capable Torch/CUDA baseline where possible;
2. keep CLaMP code/model identity pinned while adapting only the minimum dependency surface;
3. run audio and Russian-text embedding smoke;
4. measure repeatability, latency, VRAM and coexistence with MAEST+AST;
5. only if blocked, create a separate upstream-reference environment for behavioral comparison;
6. do not downgrade the stable core `.venv` merely to match research-era dependencies.

The older upstream CUDA 11.8 recipe is treated as a **reference environment description**, not as the desired RTX 5070 Ti production GPU route.

## Remaining P0 unknowns

- exact CLaMP weight variant/revision/checksum;
- exact MERT model revision;
- whether unmodified CLaMP inference runs on Python 3.12 / current Torch;
- required compatibility patches, if any;
- MERT/CLaMP peak VRAM;
- model shutdown/release behavior;
- RU text retrieval quality;
- third-party model license/release policy (#41).
