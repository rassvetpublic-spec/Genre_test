# VALIDATION BASELINE — resolver v0.2.1

Purpose: preserve diagnostic real-track evidence for resolver calibration. Audio files and absolute local paths are intentionally not stored in Git.

Model: `mtg-upf/discogs-maest-30s-pw-129e-519l`
Default windows: 5 x 30 s
Runtime used for the source runs: Python 3.12.10, PyTorch 2.11.0+cu128, CUDA 12.8, NVIDIA GeForce RTX 5070 Ti.

Important: this is **not yet a ground-truth accuracy benchmark**. The table is derived from model outputs supplied after real-track runs. Manually reviewed expected genre labels have not yet been attached to every track, so the resolver must not be tuned to force a presumed answer from a filename or prior description.

## 11-track diagnostic set

The `v0.2.1` columns below are deterministic resolver outputs calculated from the stored raw `top_styles` and `broad_genres`. The tracks should still be rerun after installation of v0.2.1 to freeze new JSON files.

| Track | Broad 1 | Broad 2 | v0.2.1 resolved | Class | Confidence | Family ratio | Style margin | Alternative style |
|---|---|---|---|---|---|---:|---:|---|
| Воли! (Новый Край 1999) | Rock 0.8136 | Pop 0.0604 | Heavy Metal | primary | high | 0.0742 | 0.5502 | Hard Rock |
| Доченька | Rock 0.9679 | Pop 0.0055 | Power Metal | primary | high | 0.0057 | 0.5779 | Heavy Metal |
| Доченька [MO] | Pop 0.4281 | Electronic 0.3066 | Vocal Pop | primary | low-medium | 0.7163 | 0.0977 | Dance-pop |
| За хутором | Pop 0.3625 | Rock 0.3464 | Pop Rock | hybrid | low-medium | 0.9556 | 0.4442 | Pop Ballad |
| Из тёмного стекла | Rock 0.7173 | Electronic 0.1475 | Alternative Rock | primary | medium | 0.2056 | 0.1419 | Pop Punk |
| По графику [MO] Final+beep | Electronic 0.4811 | Pop 0.4050 | Dance-pop | hybrid | low-medium | 0.8418 | 0.6373 | Indie Pop |
| Сашенька 18+ (Live Олимпийский) | Pop 0.4714 | Rock 0.3166 | Pop Ballad | primary | medium | 0.6717 | 0.6360 | Europop |
| Сашенька 18+ (Radio Edit) | Rock 0.5027 | Pop 0.3781 | Power Metal | primary | low-medium | 0.7520 | -0.2281 | Schlager |
| Слова другие + | Rock 0.7418 | Electronic 0.0470 | Heavy Metal | primary | medium | 0.0633 | 0.1387 | Alternative Rock |
| Слова другие 2024. acapella - Industrial SUNO | Electronic 0.5257 | Pop 0.2580 | Dance-pop | primary | high | 0.4907 | 0.4770 | Europop |
| Accordion v1 | Pop 0.3807 | Latin 0.2100 | Schlager | primary | medium | 0.5516 | 0.1609 | Tango |

## What v0.2.1 fixes

### 1. Broad-family certainty is not subgenre certainty

`Из тёмного стекла` has a clear Rock family, but Alternative Rock and Pop Punk are close. `Слова другие +` similarly has a clear Rock family while Heavy Metal and Alternative Rock are close. v0.2 called the broad-family confidence `high`; v0.2.1 lowers the final resolved-subgenre confidence to `medium`.

### 2. Cross-family fine-style conflict is visible

The Radio Edit of `Сашенька` has Rock as the leading broad family, but the strongest individual style is Pop---Schlager. The resolver still keeps the leading-family candidate `Power Metal`, but now reports `Schlager` as `secondary_style`, produces a negative `style_margin`, and lowers confidence to `low-medium` instead of hiding the disagreement.

### 3. Generic labels get context

Standalone labels such as `Ballad` and `Vocal` are weak human-facing outputs. v0.2.1 renders `Pop---Ballad` as `Pop Ballad` and `Pop---Vocal` as `Vocal Pop` while preserving the original MAEST labels in `top_styles`.

### 4. Hybrid detection uses relative evidence too

A fixed absolute margin can miss two large, nearly proportional family scores. v0.2.1 therefore marks a result hybrid when either:

- top-family absolute margin is below `0.08`; or
- secondary/primary family ratio is at least `0.80`.

### 5. Raw evidence remains untouched

`resolved_genre`, confidence and diagnostic fields are resolver outputs only. Raw `top_styles` and `broad_genres` are never rewritten, which allows future threshold changes without rerunning the neural model if the stored raw output is available.

## Current thresholds

- hybrid absolute family margin: `< 0.08`
- hybrid secondary/primary ratio: `>= 0.80`
- medium broad-family margin: `< 0.20`
- strong secondary family ratio: `>= 0.65`
- high relative fine-style margin: `>= 0.35`
- medium relative fine-style margin: `>= 0.15`

These thresholds are provisional. They should be tuned again only after manually reviewed expected labels are attached and the benchmark grows beyond the current 11 tracks.

## Next benchmark gate

1. Rerun all 11 tracks under v0.2.1.
2. Record an expected human genre/subgenre for each track without looking at the resolver result first.
3. Expand to at least 20 deliberately varied tracks.
4. Measure family accuracy, resolved-label usefulness, hybrid precision/recall and confidence calibration separately.
