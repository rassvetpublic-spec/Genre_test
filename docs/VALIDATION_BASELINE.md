# VALIDATION BASELINE — v0.2

Purpose: preserve early real-track evidence for tuning the resolver. Audio files and absolute local paths are intentionally not stored in Git.

Model: `mtg-upf/discogs-maest-30s-pw-129e-519l`
Default windows: 5 x 30 s
Runtime used for the validated Windows runs: Python 3.12.10, PyTorch 2.11.0+cu128, CUDA 12.8, NVIDIA GeForce RTX 5070 Ti.

| Track | Resolved genre | Broad family | Secondary | Classification | Confidence | Margin | BPM | Key |
|---|---|---|---|---|---|---:|---:|---|
| Из тёмного стекла | Alternative Rock* | Rock 0.7173 | Electronic 0.1475 | primary* | high* | 0.5698* | 81.52 | E minor |
| За хутором | Pop Rock | Pop 0.3625 | Rock 0.3464 | hybrid | low-medium | 0.0161 | 125.00 | C minor |
| По графику [MO] Final+beep | Dance-pop | Electronic 0.4811 | Pop 0.4050 | hybrid | low-medium | 0.0761 | 133.93 | D# minor |
| Сашенька 18+ (Live Олимпийский) | Ballad | Pop 0.4714 | Rock 0.3166 | primary | medium | 0.1547 | 81.52 | F# minor |
| Сашенька 18+ (Radio Edit) | Power Metal | Rock 0.5027 | Pop 0.3781 | primary | medium | 0.1247 | 156.25 | F# minor |

`*` The original `Из тёмного стекла` JSON was produced before resolver fields were added. The v0.2 resolver result shown here is deterministically inferred from the stored raw broad/style scores and current thresholds; rerun it under v0.2 before using it as a frozen benchmark.

## What this baseline already demonstrates

1. Broad family confidence can be high (`Из тёмного стекла`) or nearly tied (`За хутором`).
2. A single broad-family label is insufficient for hybrid material.
3. The strongest fine-grained style is often more useful to a human than the broad family (`Pop Rock`, `Dance-pop`, `Power Metal`).
4. Tempo detection can represent half/double-time ambiguities; presentation should keep alternate tempo candidates.
5. Resolver thresholds are provisional and must be calibrated on a larger manually reviewed set.

## Next benchmark gate

Collect at least 10–20 manually reviewed tracks covering intentionally different lanes: rock, pop, electronic/dance, blues, acoustic/folk, gothic/industrial, hip-hop/trap and mixed/hybrid material. Store only derived measurements unless explicit permission is given to store media.
