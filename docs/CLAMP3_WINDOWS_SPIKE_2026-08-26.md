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

Therefore the spike order was:

1. **isolated modern sidecar first** — Python 3.12 + current Blackwell-capable Torch/CUDA baseline;
2. keep CLaMP code/model identity pinned while adapting only the minimum dependency surface;
3. run audio and Russian-text embedding smoke;
4. measure repeatability, latency, VRAM and coexistence with MAEST+AST;
5. do not downgrade the stable core `.venv` merely to match research-era dependencies.

The older upstream CUDA 11.8 recipe is treated as a **reference environment description**, not as the desired RTX 5070 Ti production GPU route.

## Initial P0 unknowns

At the time of this 2026-08-26 inventory the following were unknown:

- exact CLaMP weight variant/revision/checksum;
- exact MERT model revision;
- whether the modern isolated runtime would execute real CLaMP/MERT inference;
- required compatibility patches, if any;
- MERT/CLaMP peak VRAM;
- model shutdown/release behavior;
- RU text retrieval path behavior.

## Resolution — final hardened P0 on 2026-08-27

All runtime-critical unknowns above are now resolved by PR #72 hardware evidence.

Selected runtime:

```text
architecture       isolated persistent subprocess sidecar
Python             3.12.10
Torch              2.12.1+cu130
CUDA               13.0
GPU                RTX 5070 Ti / sm_120
CLaMP variant      SAAS
CLaMP code         9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
CLaMP weight SHA   5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80
MERT revision      55fa29e5522049926c03d2ff9ae54d22c20e668f
XLM-R revision     e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
preprocessing      clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3
MERT compat        mert-weight-norm-key-remap-v1
```

The final `C:\GIT\TEST.wav` run proved:

- MAEST CUDA first;
- AudioSet AST CUDA first;
- real CLaMP/MERT audio embedding;
- Russian UTF-8 text embedding;
- direct and persistent-sidecar agreement;
- repeatability at approximately cosine 1.0;
- exact MERT state-dict loading after in-memory legacy weight-norm key translation;
- pinned MERT source checkpoint unmodified;
- live sidecar CUDA allocation >2.24 GB and peak >2.43 GB before close;
- sidecar RSS ~5.02 GB before close;
- clean process termination after shutdown;
- flat `.genre_test` state layout with all diagnostics under `.genre_test/logs`.

`core-native` inference was not executed and is not claimed. After the isolated sidecar passed the complete target-PC gate, direct core integration was classified **N/A / intentionally not selected** for v0.5 to avoid destabilizing the core environment.

See `docs/CLAMP3_RUNTIME_P0.md` for the final acceptance matrix and measured values.
