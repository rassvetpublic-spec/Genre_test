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

## v0.3.1 — runtime hardening

- [x] cooperative Safe Stop in Analysis and Validation
- [x] copy-output controls
- [x] persistent repo-local log
- [x] repo-local history/results/Hugging Face cache
- [x] safe migration from pre-v0.3.1 history
- [x] skip unreadable audio instead of aborting a large run
- [x] persist file errors into Validation JSON/CSV

## v0.3.2 — validation hardening

- [x] run full real-catalog Fast + Auto + Accurate benchmark
- [x] establish Auto vs Accurate baseline: 225/225 resolved-genre match
- [x] establish Fast vs Accurate baseline: 181/225 resolved-genre match
- [x] resolve negative-style-margin cross-family conflicts as hybrid
- [x] split current mode convergence from historical drift in reports
- [x] record worst mode pair and reason
- [x] report Fast/Auto/Accurate window counts
- [x] report Auto inference-window savings
- [x] ignore service/cache directories by default
- [x] add GUI/CLI service-directory override
- [x] add short-input QC gates
- [x] add FFmpeg/SoundFile decoder diagnostics
- [x] pin default MAEST Hugging Face revision
- [x] bump result schema to 3

## P1 — accuracy calibration

- [ ] rerun only unstable/changed tracks under v0.3.2
- [ ] compare v0.3.1 ↔ v0.3.2 resolver drift
- [ ] expand manually reviewed benchmark to 20+ intentionally different tracks
- [ ] attach manually reviewed expected genre labels
- [ ] calibrate severity/JS/Top-N thresholds against observed false alarms
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
