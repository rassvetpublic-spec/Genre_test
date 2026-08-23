# ACTIVE / CURRENT

Version: **0.2.1**

## Current implementation

- Windows-first local genre analyzer
- MAEST Discogs 519 via Transformers/PyTorch
- CUDA auto-detection; validated on Windows/NVIDIA
- 30-second representative windows
- default `Auto` analysis mode with duration-aware adaptive window count
- `Fast`, `Accurate`, and `Expert` analysis modes
- broad family aggregation plus human-readable genre resolver
- hybrid detection from absolute family margin and secondary/primary family ratio
- confidence derived from both broad-family and fine-style evidence
- alternative fine-style exposed as `secondary_style`
- raw MAEST probabilities preserved for recalibration
- BPM/key/basic spectral features
- JSON per track, CSV for batch
- CLI and Windows GUI

## Automatic analysis policy

Duration target:

- <60 s: 1 window
- 60–120 s: 3 windows
- 120–210 s: 5 windows
- 210–300 s: 7 windows
- 300–420 s: 9 windows
- >420 s: 11 windows

For long tracks, `Auto` first evaluates five windows spread across the same final grid. A stable `primary + high confidence` result stops after those five. Hybrid or lower-confidence results expand to the full duration-based target.

`Fast` uses at most three windows. `Accurate` always uses the full duration target. `Expert` exposes manual window count and Top-K.

## Resolver calibration v0.2.1

The first 11-track diagnostic set exposed a distinction that v0.2 did not model: a broad family can be very clear while the exact fine style remains ambiguous.

v0.2.1 records:

- `family_margin`
- `family_ratio`
- `style_margin`
- `secondary_genre`
- `secondary_style`
- `analysis_mode`
- `windows_analyzed`

`confidence` now reflects the resolved fine-style label, not only the winning broad family.

## Windows GUI

Launch with `scripts\gui.ps1` or double-click `scripts\Genre_test_GUI.cmd` after setup.

Default GUI exposes file/folder selection, output directory, device and analysis mode. Manual `Окон` and `Top-K` controls are hidden unless `Экспертный` is selected.

## Validated runtime

- Python 3.12.10
- PyTorch 2.11.0+cu128
- CUDA runtime 12.8
- NVIDIA GeForce RTX 5070 Ti

## Current validation status

- 11 real-track outputs collected under the previous fixed five-window workflow
- resolver failure modes identified from those outputs
- regression tests added for close fine styles, cross-family style conflict, generic labels and ratio-based hybrid detection
- automatic sampling policy has pure unit tests
- this set is diagnostic evidence, not a ground-truth accuracy benchmark

## Next validation gate

1. rerun the diagnostic tracks under v0.2.1 Auto;
2. record `analysis_mode` and `windows_analyzed`;
3. add manually reviewed expected labels;
4. expand to 20+ intentionally diverse tracks;
5. only then tune thresholds again or add a second independent model.
