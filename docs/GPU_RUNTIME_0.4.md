# Genre_test 0.4 GPU runtime

## Release baseline

Genre_test 0.4 targets the following reproducible Windows GPU runtime:

- PyTorch: **2.12.1** release baseline (`>=2.12.1` accepted by package metadata)
- CUDA wheel runtime: **13.0** (`cu130`)
- Windows/Python: Python 3.11 or 3.12 x64
- NVIDIA architecture: Turing or newer for CUDA 13.0
- Blackwell: native compiled architecture required when the active GPU reports Blackwell compute capability

Canonical install used by `scripts/setup.ps1`:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade torch==2.12.1 --index-url https://download.pytorch.org/whl/cu130
```

Official references:

- https://pytorch.org/get-started/previous-versions/
- https://github.com/pytorch/pytorch/blob/main/RELEASE.md

PyTorch's release matrix lists CUDA 13.0 as stable for 2.12 and includes Blackwell compute capabilities in the CUDA 13 Windows build matrix.

## Native Blackwell gate

`Runtime Health` does not treat `torch.cuda.is_available()` alone as sufficient. It checks:

1. PyTorch version is at least 2.12.1
2. `torch.version.cuda` starts with `13.0`
3. active device name and compute capability
4. `torch.cuda.get_arch_list()`
5. for a Blackwell device, the active `sm_xxx` must exist in the compiled architecture list

Example expected RTX 50-series health value:

```text
GPU architecture: OK | Blackwell native (sm_120)
```

If the active Blackwell GPU reports `sm_120` but the wheel does not contain `sm_120`, Runtime Health reports FAIL rather than silently accepting PTX/fallback execution.

## Setup behavior

`scripts/setup.ps1` probes the existing `.venv` before installing Torch.

If all target conditions already pass, setup prints that the compatible runtime is present and skips the multi-gigabyte Torch reinstall.

If the runtime is missing or mismatched, setup installs the pinned 2.12.1 `cu130` wheel and probes again.

`pip`'s normal user cache remains shared between virtual environments, so a wheel already downloaded by another Python project can be reused from the local pip cache. Each project still keeps its own isolated `.venv`; only the download cache is shared.

## CPU fallback

CPU remains supported as a degraded mode. PyTorch >=2.12.1 CPU builds are accepted, but Runtime Health reports CUDA/GPU as WARN because the 0.4 accelerated release target is CUDA 13.0.

## CI

Lightweight GitHub CI intentionally does not download the multi-gigabyte Torch CUDA wheel. CI gates:

- package metadata requires `torch>=2.12.1`
- PowerShell `setup.ps1` parses successfully
- setup contains the `cu130` installation route
- unit tests validate CUDA 13 rejection/acceptance and native Blackwell detection with mocked Torch runtime objects

A real Windows Blackwell CUDA smoke remains required before merging v0.4.0.
