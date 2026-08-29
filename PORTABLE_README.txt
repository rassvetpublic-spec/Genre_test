Genre_test portable packaging

STATUS
------
There is currently no published stable portable release.
The active development version is read from pyproject.toml.

START
-----
1. Extract a future packaged build to a normal local folder.
2. Do not run directly from inside a ZIP.
3. Start only Genre_test_START.cmd.
4. Internet access may be required for first-time dependency/model setup.

RUNTIME BASELINE
----------------
- Windows 10/11 x64
- Windows PowerShell 5.1 for packaged bootstrap
- Python 3.11 / 3.12 / 3.13 x64
- PyTorch 2.12.1
- NVIDIA CUDA 13.0 / cu130 when NVIDIA hardware is used
- CPU-only mode supported
- FFmpeg
- isolated project .venv

The package must not bundle another project's virtual environment.
Normal pip and Hugging Face user caches may be reused.

MODELS
------
Pinned public analysis models are downloaded on demand.
Third-party model provenance remains documented separately.

INTEGRITY
---------
A future published package must provide its own checksum manifest.
Do not use checksum files from retired releases.

Current development line: Genre_test 0.5.0.dev0
