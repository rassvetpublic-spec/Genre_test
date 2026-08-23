# ACTIVE / CURRENT

Version: **0.2.0**

## Current implementation

- Windows-first local genre analyzer
- MAEST Discogs 519 via Transformers/PyTorch
- CUDA auto-detection; tested on Windows with NVIDIA GeForce RTX 5070 Ti
- 5 representative 30-second windows by default
- broad family aggregation plus human-readable genre resolver
- hybrid detection from top-family margin
- confidence label and raw MAEST preservation
- BPM/key/basic spectral features
- JSON per track, CSV for batch
- CLI and Windows GUI

## Windows GUI

Launch with `scripts\gui.ps1` or double-click `scripts\Genre_test_GUI.cmd` after setup.
The GUI supports native file/folder selection, output directory selection, device, windows, Top-K, progress/status and result preview.

## Validated runtime

- Python 3.12.10
- PyTorch 2.11.0+cu128
- CUDA runtime 12.8
- NVIDIA GeForce RTX 5070 Ti

## Next validation gate

Run a deliberately diverse test set (rock, blues, gothic/industrial, trap/pop, acoustic) and compare resolved labels against human classification before adding a second independent model.
