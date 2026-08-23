# VALIDATION BASELINE — v0.2 / v0.2.1 diagnostic set

Purpose: preserve real-track evidence for tuning the resolver. Audio files and absolute local paths are intentionally not stored in Git.

Model: `mtg-upf/discogs-maest-30s-pw-129e-519l`
Window length: 30 s

The rows below were produced with the earlier **fixed 5-window** workflow unless explicitly noted. They are retained as a diagnostic baseline. v0.2.1 introduces adaptive `Auto`; tracks should be rerun before using these rows as a current benchmark.

| Track | v0.2 resolved | Broad family | Secondary | Classification | Confidence | Margin | BPM | Key |
|---|---|---|---|---|---|---:|---:|---|
| Из тёмного стекла | Alternative Rock* | Rock 0.7173 | Electronic 0.1475 | primary* | high* | 0.5698* | 81.52 | E minor |
| За хутором | Pop Rock | Pop 0.3625 | Rock 0.3464 | hybrid | low-medium | 0.0161 | 125.00 | C minor |
| По графику [MO] Final+beep | Dance-pop | Electronic 0.4811 | Pop 0.4050 | hybrid | low-medium | 0.0761 | 133.93 | D# minor |
| Сашенька 18+ (Live Олимпийский) | Ballad | Pop 0.4714 | Rock 0.3166 | primary | medium | 0.1547 | 81.52 | F# minor |
| Сашенька 18+ (Radio Edit) | Power Metal | Rock 0.5027 | Pop 0.3781 | primary | medium | 0.1247 | 156.25 | F# minor |
| Воли! (Новый Край 1999) | Heavy Metal | Rock 0.8136 | Pop 0.0604 | primary | high | 0.7533 | 133.93 | B major |
| Доченька [MO] | Vocal | Pop 0.4281 | Electronic 0.3066 | primary | medium | 0.1215 | 144.23 | G minor |
| Доченька | Power Metal | Rock 0.9679 | Pop 0.0055 | primary | high | 0.9624 | 156.25 | D# minor |
| Слова другие + | Heavy Metal | Rock 0.7418 | Electronic 0.0470 | primary | high | 0.6948 | 89.29 | G minor |
| Слова другие 2024 acapella - Industrial SUNO | Dance-pop | Electronic 0.5257 | Pop 0.2580 | primary | high | 0.2677 | 133.93 | B minor |
| Accordion v1 | Schlager | Pop 0.3807 | Latin 0.2100 | primary | medium | 0.1707 | 156.25 | D major |

`*` The original `Из тёмного стекла` JSON was produced before resolver fields were added; its v0.2 resolver row was inferred deterministically from the stored raw scores.

## Resolver findings from this set

1. Broad-family certainty and exact fine-style certainty are different quantities.
2. Close fine styles must lower resolved-subgenre confidence even when the winning broad family is clear.
3. A strong competing style can belong to the secondary broad family and should be exposed instead of hidden.
4. Generic leaves such as `Ballad` and `Vocal` need family context in human-facing output.
5. Hybrid detection benefits from both absolute family margin and secondary/primary family ratio.
6. The set is diagnostic evidence only; filenames and assumed song intent are not ground truth labels.

## v0.2.1 Auto rerun gate

Rerun the set with default `Auto` and record:

- resolved genre
- primary/secondary family
- confidence
- family ratio
- style margin
- secondary style
- `analysis_mode`
- `windows_analyzed`
- runtime

Then compare selected tracks with `Accurate` mode. If Auto stops at 5 windows but Accurate materially changes the genre decision, the early-stop policy needs recalibration.

## Next benchmark gate

Attach manually reviewed expected labels and expand to at least 20 intentionally diverse tracks before making accuracy claims or adding a second independent model.
