Genre_test 0.3.6 Portable prerelease
====================================

START
-----
1. Extract the ZIP to a normal writable folder (for example D:\Genre_test).
2. Make sure the PC is connected to the Internet for the first start.
3. Double-click: Genre_test_START.cmd
4. Wait for Setup / Diagnostics to finish. The GUI opens automatically.

The user does NOT need to open PowerShell, create a virtual environment, install Python packages or configure FFmpeg manually.

FIRST START MAY INSTALL
-----------------------
- Python 3.12 x64 (if Python 3.11/3.12 x64 is absent)
- PyTorch CUDA 12.8 build when an NVIDIA GPU is detected
- CPU PyTorch build when NVIDIA is not detected
- Genre_test Python runtime dependencies
- FFmpeg (Gyan.FFmpeg)

The pinned MAEST model is downloaded automatically during the first audio analysis and cached under .genre_test\huggingface.

REPEATED STARTS
---------------
Run Genre_test_START.cmd again. Existing .venv, Python, PyTorch and FFmpeg are reused after checks, so startup is much faster.

REQUIREMENTS
------------
- Windows 10/11 x64
- Internet connection for first installation/model download
- Windows Package Manager (winget / App Installer) when Python or FFmpeg must be installed
- Recommended free disk space before first setup: 8 GB or more

If winget is missing, the launcher opens the Microsoft Store App Installer page and stops with an explanation.

DIAGNOSTICS / LOGS
------------------
Bootstrap log: .genre_test\bootstrap.log
Application log: .genre_test\logs\genre_test.log
Runtime dependency status is also available from the GUI button "Зависимости...".

This prerelease is based on Genre_test 0.3.6 (main commit 06afdc5cb4d940797e514873e34b737ef0250540).
