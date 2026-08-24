Genre_test 0.3.6 Portable prerelease

REQUIRED INSTALL LOCATION
-------------------------
Extract the ZIP directly to C:\.
The resulting folder MUST be:

  C:\Genre_test_0.3.6_portable

Start only:

  C:\Genre_test_0.3.6_portable\Genre_test_START.cmd

The launcher intentionally refuses to run from Downloads, Desktop, D:\, network paths, nested folders, or directly inside the ZIP. The fixed ASCII path avoids Windows/PyTorch DLL and Unicode-path problems in this prerelease.

FIRST RUN
---------
The launcher uses stock Windows PowerShell 5.1. PowerShell 7 is not required.

It checks/repairs WinGet, Microsoft Visual C++ 2015-2022 x64 Runtime, Python 3.11/3.12 x64, the local .venv, PyTorch CUDA 12.8 or CPU PyTorch, FFmpeg and Genre_test dependencies. It then runs Runtime Health, genre-test --version and genre-test doctor before opening the GUI.

If WinGet is missing, the package first attempts Microsoft's Microsoft.WinGet.Client + Repair-WinGetPackageManager recovery path. Microsoft Store App Installer is only the final fallback.

If PyTorch import fails, the launcher writes the complete error to:

  C:\Genre_test_0.3.6_portable\.genre_test\torch_import_diagnostic.txt

Bootstrap log:

  C:\Genre_test_0.3.6_portable\.genre_test\bootstrap.log

The first analysis may download the pinned MAEST model. Internet access is required for first-time setup/model download.

Genre_test 0.3.6 Portable prerelease
Frozen source base: main commit 06afdc5cb4d940797e514873e34b737ef0250540
