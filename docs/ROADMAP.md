# ROADMAP

## v0.2 — implemented

- [x] Windows GUI / native input file dialog
- [x] batch folder selection
- [x] resolved genre
- [x] broad-family hybrid detection
- [x] confidence / family margin
- [x] half/double tempo candidates in presentation
- [x] raw MAEST data retained
- [x] Windows CUDA P0 run

## v0.2.1 — resolver calibration

- [x] collect 11 real-track diagnostic outputs
- [x] add secondary/primary family ratio
- [x] add relative fine-style margin
- [x] expose strongest competing fine style
- [x] lower resolved-subgenre confidence when fine styles are close
- [x] ratio-based hybrid detection
- [x] contextualize generic labels such as `Ballad` and `Vocal`
- [x] add regression tests for observed failure patterns
- [ ] rerun all 11 tracks under v0.2.1
- [ ] attach manually reviewed expected genre labels

## P1 — validation

- [ ] expand benchmark to 20+ known tracks across intentionally different genres
- [ ] tune resolver thresholds against manually reviewed expected labels
- [ ] pin the MAEST Hugging Face revision for reproducibility
- [ ] improve key/BPM validation
- [ ] add HF authentication status to `doctor`

## P2 — ensemble

- [ ] add an independent tagger/classifier
- [ ] calibrate ensemble scores
- [ ] map model taxonomies into a stable internal genre ontology

## P3 — product modes

- [ ] distributor-oriented broad genre/subgenre
- [ ] Suno Style handoff
- [ ] catalog comparison / similarity
- [ ] optional XLSX/HTML report
