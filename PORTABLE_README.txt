Genre_test 0.4.0 Portable Release

QUICK START
-----------
1. Extract Genre_test_0.4.0_portable.zip to a normal local folder. A short ASCII path such as C:\Genre_test_0.4.0_portable is recommended, but no fixed install path is required.
2. Do not run directly from inside the ZIP.
3. Start only Genre_test_START.cmd.
4. Internet access is required on the first setup/model download.

FIRST RUN
---------
The packaged launcher uses stock Windows PowerShell 5.1 and scripts\release_bootstrap.ps1. PowerShell 7 is not required for the portable release.

The bootstrap checks/prepares:
- WinGet / App Installer recovery;
- Microsoft Visual C++ 2015-2022 x64 Runtime;
- Python 3.11, 3.12 or 3.13 x64 (3.13 is preferred when already installed; Python 3.12 is installed only if no compatible Python exists);
- private .venv inside the extracted Genre_test folder;
- PyTorch 2.12.1;
- NVIDIA: CUDA 13.0 / cu130, with native active architecture required on Blackwell (including sm_120);
- CPU-only systems: PyTorch CPU build;
- FFmpeg;
- Genre_test dependencies;
- genre-test --version and genre-test doctor before GUI start.

PyTorch is not downloaded again when the existing release .venv already satisfies the runtime gates. Normal pip and Hugging Face caches remain shared in the user profile; another project's .venv is never reused directly.

GPU BEHAVIOR
------------
NVIDIA hardware detection uses nvidia-smi when available and Windows PnP/CIM hardware detection as fallback. If NVIDIA hardware exists but PyTorch CUDA 13/native-architecture checks fail, setup stops with a clear error instead of silently switching to CPU.

On a true CPU-only computer, CPU PyTorch is valid and Runtime Health reports CUDA/GPU as N/A.

MODELS
------
The first analysis may download the pinned MAEST Discogs519 and AudioSet AST models from Hugging Face. Anonymous access is sufficient for these public pinned models. Model downloads are cached normally and are not included in the ZIP.

LOGS
----
Bootstrap log:
  .genre_test\bootstrap.log

PyTorch import diagnostics:
  .genre_test\torch_import_diagnostic.txt

Application log:
  .genre_test\logs\genre_test.log

REPEATED START
--------------
Run Genre_test_START.cmd again. Compatible Python, .venv, PyTorch and FFmpeg are reused after validation. Moving the extracted folder after .venv has been created is not recommended; extract to the final location before first launch.

SYSTEM REQUIREMENTS
-------------------
- Windows 10/11 x64
- Windows PowerShell 5.1
- Internet on first setup/model download
- sufficient disk space for Python/PyTorch/models (several GB can be required)
- NVIDIA is optional; CPU fallback is supported

PACKAGE INTEGRITY
-----------------
Compare the ZIP SHA-256 with SHA256SUMS.txt from the GitHub Release.

Version: Genre_test 0.4.0
