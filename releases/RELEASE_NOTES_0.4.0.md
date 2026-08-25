# Genre_test v0.4.0

Genre_test 0.4.0 is the first full ensemble/validation release built around MAEST Discogs519 + pinned AudioSet AST.

## Highlights

- `AudioProfile` schema 4 with Normal / SUNO / Distributor views.
- Pinned MAEST genre classifier plus independent AudioSet AST semantic evidence for vocals, instruments, mood and production.
- Genre/Family reconciliation prevents contradictory published profiles.
- Weak AudioSet genre evidence keeps its absolute confidence and cannot receive a full semantic vote merely by being the only mapped AST tag.
- Tempo-v2 with half/double and short-loop 3:2 handling.
- Native source audio metadata is reported independently from the internal MAEST analysis stream.
- Validation and saved-build comparison are separate workflows with build-aware history identity and explicit `DRIFT` terminology.
- Dark theme is default; Dark/Light can be switched live.
- Safe Stop and live GUI presentation/device/mode controls.

## Runtime

- Python 3.11 / 3.12 / 3.13 x64.
- PyTorch 2.12.1 installation target.
- NVIDIA: CUDA 13.0 / cu130.
- Blackwell requires native active architecture; RTX 5070 Ti / `sm_120` was verified in the Windows release smoke.
- CPU-only computers are supported with CPU PyTorch and report CUDA/GPU as N/A.
- Public pinned Hugging Face models work anonymously; a token is optional.

## Portable package

`Genre_test_0.4.0_portable.zip` contains source/runtime bootstrap files, not Python, PyTorch or model weights. On first launch `Genre_test_START.cmd` prepares a private `.venv`, WinGet/VC++/Python/PyTorch/FFmpeg dependencies and runs `genre-test doctor` before opening the GUI.

Compatible installed Python and PyTorch are reused. Normal pip and Hugging Face caches are shared through the user profile; another project's `.venv` is never reused directly.

Verify the archive with `SHA256SUMS.txt`.

## Release validation

- Current Windows Auto regression batch: 25/25 files completed, semantic profiles 25/25, file errors 0.
- Accurate Validation batch: 25/25 files completed, file errors 0.
- Windows GPU runtime health: Deps 12/12, CUDA OK, GPU OK, FFmpeg OK, HF OK.
- GitHub CI: Python 3.11 / 3.12 / 3.13, Ruff, pytest, launcher, PowerShell and CUDA/Blackwell gates.

## Known diagnostic / development items

- AudioSet AST currently decodes semantic audio separately from the MAEST path; shared decode/cache remains a later optimization.
- Classical period/style interpretation requires a dedicated resolver; MAEST `Classical` should not be treated as proof of historical period.
- A non-fatal Transformers zero-mel-filter warning can appear during AST preprocessing and is intentionally tracked rather than hidden.
- The xLaunge test track remains a registered mode-convergence case (Auto vs Fast/Accurate).
- The short 3:2 tempo regression's observed ~170 BPM remains an observed test result; independent ground-truth labeling is still tracked separately.
