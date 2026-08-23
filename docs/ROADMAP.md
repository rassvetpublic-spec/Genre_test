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

## v0.2.1 — resolver calibration and Auto analysis

- [x] collect 11 real-track diagnostic outputs
- [x] add secondary/primary family ratio
- [x] add relative fine-style margin
- [x] expose strongest competing fine style
- [x] lower resolved-subgenre confidence when fine styles are close
- [x] ratio-based hybrid detection
- [x] contextualize generic labels such as `Ballad` and `Vocal`
- [x] add duration-aware automatic window target
- [x] adaptive early stop for stable high-confidence results
- [x] `Fast`, `Accurate`, `Expert` modes
- [x] hide manual windows/Top-K outside Expert GUI mode
- [x] record `analysis_mode` and `windows_analyzed`

## v0.3.0 — Validation Lab

- [x] SHA-256 content identity independent of path
- [x] duplicate-file detection across scattered catalogs
- [x] local SQLite history
- [x] path/size/mtime hash cache
- [x] versioned immutable run JSON snapshots
- [x] analyzer/schema/run/timestamp/Git metadata
- [x] raw style/broad score history
- [x] validation-session history
- [x] shared Fast/Auto/Accurate prediction cache
- [x] pairwise mode convergence
- [x] Jensen-Shannon broad-distribution drift
- [x] cosine broad-distribution similarity
- [x] weighted Top-N style overlap
- [x] half/double-time-aware BPM comparison
- [x] key/mode comparison
- [x] STABLE / MINOR / SIGNIFICANT / CRITICAL severity
- [x] HIGH / MEDIUM / LOW / FAIL convergence
- [x] all / old_versions / unstable recheck filters
- [x] legacy `*.genre*.json` history import
- [x] analyzer-version comparison summary + JSON/CSV
- [x] Validation GUI tab
- [x] CLI `validate`, `history-import`, `compare-versions`
- [x] pure regression tests for identity/history/comparison/convergence/filtering

## P1 — real-data validation

- [ ] import the existing historical result JSON set into v0.3 history
- [ ] rerun diagnostic tracks with v0.3 `Fast + Auto + Accurate`
- [ ] measure Auto ↔ Accurate convergence and runtime
- [ ] expand manually reviewed benchmark to 20+ intentionally different tracks
- [ ] attach manually reviewed expected genre labels
- [ ] calibrate severity/JS/Top-N thresholds against observed false alarms
- [ ] pin the MAEST Hugging Face revision for strict reproducibility
- [ ] improve key/BPM validation
- [ ] add HF authentication status to `doctor`

## P2 — benchmark / ensemble

- [ ] explicit ground-truth table separate from run history
- [ ] accuracy metrics by broad family and fine style
- [ ] add an independent tagger/classifier
- [ ] compare single-model vs ensemble accuracy/drift
- [ ] map model taxonomies into a stable internal genre ontology

## P3 — product modes

- [ ] distributor-oriented broad genre/subgenre
- [ ] Suno Style handoff
- [ ] catalog similarity / nearest tracks
- [ ] optional XLSX/HTML dashboard
