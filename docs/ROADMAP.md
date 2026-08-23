# ROADMAP

## v0.2 — implemented

- [x] Windows GUI / native input file dialog
- [x] batch folder selection
- [x] resolved genre
- [x] broad-family hybrid detection
- [x] confidence / family margin
- [x] half/double tempo candidates in presentation
- [x] raw MAEST data retained
- [x] Windows CUDA P0 run on RTX 5070 Ti

## P1 — validation

- [ ] benchmark on 10–20 known tracks across intentionally different genres
- [ ] tune hybrid/confidence thresholds from observed errors
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
