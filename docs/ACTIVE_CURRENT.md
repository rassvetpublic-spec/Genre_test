# ACTIVE / CURRENT

Status: MVP v0.1 scaffolded

## Current objective

Get a reproducible local genre report from one WAV/MP3 on Windows.

## Current engine

- primary: `mtg-upf/discogs-maest-30s-pw-129e-519l`
- inference: PyTorch / Transformers
- segmentation: five uniform 30 s windows
- features: librosa BPM/key/spectral summary
- output: JSON + batch CSV

## P0 gate

Before adding more ML models, verify on real tracks:

1. environment installs on the target Windows machine;
2. CUDA is detected when expected;
3. one full WAV completes without crash;
4. output labels are plausible;
5. same file produces stable scores across repeated runs;
6. CPU fallback works.

Only after P0: add ensemble/calibration.
