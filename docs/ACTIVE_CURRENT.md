# ACTIVE / CURRENT

Version: **0.2.1**

## Current implementation

- Windows-first local genre analyzer
- MAEST Discogs 519 via Transformers/PyTorch
- CUDA auto-detection; validated on Windows/NVIDIA
- 5 representative 30-second windows by default
- broad family aggregation plus human-readable genre resolver
- hybrid detection from absolute family margin and secondary/primary family ratio
- confidence derived from both broad-family and fine-style evidence
- alternative fine-style exposed as `secondary_style`
- raw MAEST probabilities preserved for recalibration
- BPM/key/basic spectral features
- JSON per track, CSV for batch
- CLI and Windows GUI

## Resolver calibration v0.2.1

The first 11-track diagnostic set exposed a distinction that v0.2 did not model: a broad family can be very clear while the exact fine style remains ambiguous.

v0.2.1 therefore records:

- `family_margin`
- `family_ratio`
- `style_margin`
- `secondary_genre`
- `secondary_style`

`confidence` now reflects the resolved fine-style label, not only the winning broad family.

## Windows GUI

Launch with `scripts\gui.ps1` or double-click `scripts\Genre_test_GUI.cmd` after setup.
The GUI supports native file/folder selection, output directory selection, device, windows, Top-K, progress/status and result preview.

## Validated runtime

- Python 3.12.10
- PyTorch 2.11.0+cu128
- CUDA runtime 12.8
- NVIDIA GeForce RTX 5070 Ti

## Current validation status

- 11 real-track outputs collected
- resolver failure modes identified from those outputs
- regression tests added for close fine styles, cross-family style conflict, generic labels and ratio-based hybrid detection
- this set is diagnostic evidence, not a ground-truth accuracy benchmark: manually reviewed expected genre labels are still required before claiming accuracy

## Next validation gate

1. rerun the 11 tracks under v0.2.1;
2. add manually reviewed expected labels for each track;
3. expand to 20+ intentionally diverse tracks;
4. only then tune thresholds again or add a second independent model.
