# Genre_test GPU runtime

## Runtime baseline

Genre_test targets the following reproducible Windows GPU runtime:

- PyTorch: **2.12.1** release baseline (`>=2.12.1` accepted by package metadata)
- CUDA wheel runtime: **13.0** (`cu130`)
- Windows/Python: **Python 3.13 x64 primary**, Python 3.12 x64 supported fallback; Python 3.11 is not supported
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

`scripts/setup.ps1` probes Python 3.13 first and Python 3.12 second. If neither supported x64 runtime is present and installation is authorized, setup installs Python 3.13 x64. Python 3.11 is outside the active core support contract.

`scripts/setup.ps1` probes the existing `.venv` before installing Torch.

If all target conditions already pass, setup prints that the compatible runtime is present and skips the multi-gigabyte Torch reinstall.

If the runtime is missing or mismatched, setup installs the pinned 2.12.1 `cu130` wheel and probes again.

`pip`'s normal user cache remains shared between virtual environments, so a wheel already downloaded by another Python project can be reused from the local pip cache. Each project still keeps its own isolated `.venv`; only the download cache is shared.

## CPU fallback

CPU remains supported as a degraded mode. PyTorch >=2.12.1 CPU builds are accepted, but Runtime Health reports CUDA/GPU as WARN because the accelerated runtime target is CUDA 13.0.

## CI

Lightweight GitHub CI intentionally does not download the multi-gigabyte Torch CUDA wheel. CI uses Python 3.13 as the primary quality/runtime-contract baseline and Python 3.12 only for compatibility pytest coverage. Static launcher/PowerShell/manifest/Ruff gates therefore run once instead of once per Python version.

Documentation-only pull requests use the lightweight path: they skip heavy Python setup, Ruff and the full pytest suite, but run lightweight repository contract tests on Python 3.13. The required `test (...)` contexts propagate preflight failures instead of becoming non-blocking skips. After merge, `main` receives only a lightweight Python 3.13 merged-tree smoke instead of a second full compatibility suite.

A real Windows Blackwell CUDA smoke remains required before publishing a packaged release.
