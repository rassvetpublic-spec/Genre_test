# CLaMP 3 TODO

Parent epic: #26

This checklist is the execution order. GitHub issues are the source of truth for acceptance criteria.

Scope boundary: [`CLAMP3_OUTPUT_SCOPE.md`](CLAMP3_OUTPUT_SCOPE.md)  
Deferred ideas: [`FAR_TODO.md`](FAR_TODO.md)

## P0 — must be completed before catalog indexing

### #27 Runtime compatibility spike
- [x] record current Genre_test core baseline
- [x] capture CLaMP upstream code snapshot
- [x] capture upstream requirement set
- [x] document provisional sidecar architecture
- [x] add no-download core health contract/probe
- [x] capture real Windows target inventory
- [x] confirm RTX 5070 Ti / `sm_120` / Torch 2.12.1+cu130 baseline
- [x] prioritize modern Python 3.12 Blackwell-capable isolated sidecar
- [x] choose exact CLaMP weight variant: SAAS for audio retrieval
- [x] pin SAAS weight revision, filename, size and SHA-256
- [x] choose exact MERT revision compatible with the pinned CLaMP extractor
- [x] build modern isolated Windows runtime on the target machine
- [x] audio embedding smoke
- [x] Russian text embedding smoke
- [x] measure repeatability
- [x] measure cold/warm latency
- [x] measure VRAM/RAM
- [x] test after MAEST+AST CUDA usage
- [x] document core-native disposition: **N/A / intentionally not selected** after isolated sidecar passed; no core-native inference is claimed
- [x] write final runtime decision: isolated persistent subprocess sidecar
- [x] hardened target-PC P0 gate PASS on 2026-08-27 (`1cef99d` hardware evidence)

Acceptance note: initial environment-creation time and complete first-download time were not retained as normalized historical metrics. This is documented in `CLAMP3_RUNTIME_P0.md`; it does not block the selected runtime correctness/architecture acceptance.

### #41 Licensing/provenance
- [x] record CLaMP MIT metadata
- [x] identify MERT CC-BY-NC-4.0 gate
- [x] prohibit bundled MERT weights pending review
- [x] pin CLaMP selected SAAS weight license/revision/SHA-256
- [x] pin MERT revision and non-commercial license policy
- [x] record XLM-R model/tokenizer revision and license
- [ ] record inference-only dependency licenses
- [ ] prepare attribution text
- [ ] state final v0.5 retrieval commercial/non-commercial policy in release notes

### #28 Retrieval schema/protocol
- [x] create pure-core retrieval package
- [x] add backend model fingerprint
- [x] add audio/text/segment embedding identity
- [x] require L2-normalized vector contract
- [x] add backend Protocol
- [x] add fake-backend tests
- [x] add serialization round-trip helpers
- [x] finalize retrieval SQLite schema v1
- [x] add explicit schema migration coverage: v1 -> v2 query-history schema
- [x] define sidecar protocol version 1
- [x] define structured sidecar error codes

### #29 Real CLaMP+MERT backend
Persistent backend implementation is in main from earlier P0 work; PR #72 supplies the final hardened target-PC hardware evidence and MERT compatibility correction.

- [x] MERT adapter implemented
- [x] corrected upstream-compatible preprocessing v3 pinned in runtime manifest
- [x] versioned in-memory `mert-weight-norm-key-remap-v1`
- [x] verify pinned MERT source checkpoint is not modified
- [x] verify MERT loads with no missing/unexpected/mismatched keys
- [x] CLaMP audio adapter implemented
- [x] CLaMP multilingual text adapter implemented
- [x] persistent subprocess handshake implemented
- [x] stable f32 little-endian/base64 vector transport
- [x] lazy CLaMP/MERT loading
- [x] clean shutdown / CUDA cache release path
- [x] structured missing model / OOM / invalid request / inference errors
- [x] keep model/library stdout off JSON protocol stdout
- [x] end-to-end core -> persistent sidecar smoke command implemented
- [x] real Windows text/audio sidecar smoke
- [x] Russian UTF-8 direct/sidecar equality
- [x] repeatability evidence on target hardware
- [x] direct/sidecar cross-path text/audio consistency
- [x] authoritative sidecar RAM + in-process CUDA metrics
- [x] verify VRAM lifecycle after shutdown via live in-process CUDA allocation + process termination
- [x] hardened target-PC P0 gate PASS

### #30 Cache/index
Implementation block: #73 / PR #75. Code completion is separate from the upcoming real-catalog acceptance run.

- [x] `retrieval.sqlite3` schema v1 foundation
- [x] v2 migration for retrieval-only query history
- [x] track/text/segment embedding persistence contract
- [x] vector SHA-256 integrity
- [x] stale backend separation by backend fingerprint
- [x] transactional SQLite vector writes
- [x] cache hit/miss/corrupt/stale accounting
- [x] exact dense float32 cosine matrix index
- [x] deterministic explicit tie-break ranking
- [x] incremental catalog orchestration from existing `history.sqlite3`
- [x] moved byte-identical files reuse `track_id` cache without re-embedding
- [x] resumable per-track commits and `--limit` pilot mode
- [x] incremental `index` acts as missing/stale-only current-backend pass
- [x] active-backend `rebuild` while retaining old backend fingerprint records
- [x] status reports current/missing/stale/corrupt/path availability
- [ ] target catalog first-pass coverage >=99% or explained failures
- [ ] target catalog second pass proves zero recomputation
- [ ] archive full-catalog index throughput/report

## P1 — product retrieval

### #31 Audio similarity
Implementation foundation: #73 / PR #75. Full-catalog performance and manual relevance acceptance remain open.

- [x] full-track query
- [x] self-match include/exclude policy
- [x] deterministic Top-K exact ranking
- [x] family/genre filters
- [x] BPM filter
- [x] key filter
- [x] confidence filter
- [x] vocal/mood/instrument/production filters
- [x] source-folder filter
- [x] AudioProfile metadata enrichment in results
- [x] separate embedding/ranking latency
- [x] explicit JSON/CSV export
- [ ] real-catalog self-match sanity near 1.0
- [ ] real-catalog Top-10/50/100 latency benchmark
- [ ] manual similarity relevance acceptance

### #32 Russian text search
Implementation foundation: #73 / PR #75. Paired RU/EN relevance benchmark remains open.

- [x] RU UTF-8 text embedding proven on real CLaMP runtime by #27/#29 P0
- [x] native RU baseline without LLM rewrite
- [x] text Top-K exact search against catalog audio vectors
- [x] text embedding cache by backend/query identity
- [x] local query history in `retrieval.sqlite3`, separate from analysis history
- [x] empty/oversized query handling
- [x] corrupt text-cache recovery
- [x] separate embedding/ranking latency
- [x] explicit JSON/CSV export
- [ ] paired RU/EN reviewed benchmark
- [ ] manual Russian search relevance acceptance

### #33 Segments
- [ ] segment policy benchmark
- [ ] 30 s baseline windows
- [ ] segment persistence integration
- [ ] centroid representative selector
- [ ] representative search
- [ ] custom interval search
- [ ] estimate full-catalog segment storage/time

### #43 Core Sound deterministic description
- [ ] version description/template rules
- [ ] map each phrase to structured evidence
- [ ] deterministic Normal description
- [ ] compact SUNO-facing ordering
- [ ] missing/weak evidence fallback
- [ ] conflicting evidence tests
- [ ] JSON/text output integration

### #34 GUI
- [ ] Catalog tab
- [ ] Search tab
- [ ] Retrieval health in top bar
- [ ] indexing progress/ETA/cache hits
- [ ] Safe Stop
- [ ] filters/results table
- [ ] theme integration
- [ ] export

### #35 CLI
PR #75 adds a dedicated lightweight `genre-test-retrieval` entry point; root-launcher unification remains separate.

- [ ] retrieval-doctor
- [x] index
- [x] index-status (`status`)
- [x] search-text
- [x] search-audio
- [x] reindex --stale-only semantics (`index` skips current cache hits)
- [x] explicit active-backend rebuild
- [x] retrieval query-history command
- [ ] stable documented exit codes
- [ ] root `Genre_test_START.cmd` command aliases
- [ ] Cyrillic path/query real-machine tests

### #36 Benchmark
- [ ] reviewed relevance schema
- [ ] >=50 queries minimum
- [ ] target >=100 queries
- [ ] Precision@K
- [ ] Recall@K
- [ ] MRR
- [ ] nDCG@K
- [ ] RU/EN overlap
- [ ] P50/P95 latency
- [ ] index throughput
- [ ] baseline report by backend fingerprint

## P2 — graduation

### #37 Zero-shot descriptors
- [ ] mood vocabulary
- [ ] character vocabulary
- [ ] movement/groove vocabulary
- [ ] energy vocabulary
- [ ] small vocal presence/style vocabulary
- [ ] production era / sonic decade vocabulary
- [ ] raw cosine score report
- [ ] manual calibration
- [ ] publish only validated descriptors

### #44 Tempo / Structure Map
- [ ] versioned tempo-segment schema
- [ ] per-segment tempo + ambiguity
- [ ] jitter smoothing policy
- [ ] sustained change-point detector
- [ ] distinguish tempo vs rhythm/energy change
- [ ] steady-tempo false-positive fixtures
- [ ] beat-switch / multi-tempo fixtures
- [ ] timeline JSON/text output
- [ ] keep global tempo-v2 backward compatibility

### #61 Alternative multilingual retrieval backends
Baseline remains **CLaMP 3 SAAS + MERT + XLM-R** until benchmark evidence supports a change.

- [ ] pin ML-CLAP code/model identity and checkpoint license
- [ ] implement experimental ML-CLAP/SONAR backend behind the Genre_test retrieval contract
- [ ] explicitly test Russian Cyrillic queries; do not assume Russian support from multilingual claims
- [ ] pin GLAP code/model identity and checkpoint license
- [ ] implement experimental GLAP backend behind the same retrieval contract
- [ ] explicitly test Russian Cyrillic queries for GLAP
- [ ] reuse the same reviewed RU/EN query set and catalog slice as #36
- [ ] compare Precision@10 / Recall@10 / nDCG@10 / MRR / RU↔EN overlap
- [ ] compare text/audio latency, indexing throughput, VRAM/RAM and disk footprint
- [ ] keep different backend identities in separate embedding matrices
- [ ] allow an XLM-V experiment only with a valid learned audio↔text alignment; never swap XLM-V into old CLaMP weights directly
- [ ] publish a backend comparison report before any default switch
- [ ] require explicit MTD for changing the default retrieval backend

### #38 Windows/portable
- [ ] optional retrieval installer
- [ ] separate runtime lifecycle
- [ ] model cache management
- [ ] resumable downloads
- [ ] corruption/checksum gate
- [ ] CPU behavior
- [ ] portable smoke

### #39 Existing catalog
- [ ] resolve source root(s)
- [x] reuse v0.4 track_id/profile metadata in retrieval orchestration
- [x] embed only retrieval layer; no MAEST/AST re-analysis in index path
- [x] resume semantics through per-track transactional cache commits
- [ ] explicit Safe Stop UX/reporting
- [ ] >=99% coverage or explained failures
- [ ] second-pass cache verification on real catalog
- [ ] index report
- [ ] backup/restore instructions

### #40 v0.5 release
- [ ] Russian README updated
- [ ] architecture docs final
- [ ] runtime docs final
- [ ] benchmark docs final
- [ ] third-party model docs final
- [ ] output-scope/FAR TODO docs final
- [ ] core v0.4 regression green
- [ ] retrieval tests green
- [ ] GPU/CPU smoke green
- [ ] catalog index report archived
- [ ] RU search manually accepted
- [ ] similarity manually accepted
- [ ] portable accepted
- [ ] explicit MTD
- [ ] branch cleanup
- [ ] release v0.5

## FAR TODO — explicitly not a v0.5 release blocker

The following remain documented but are not pulled into active implementation until a validated evidence source exists:

- rich vocal register/timbre/diction/spatial profile;
- detailed kick/snare/hat/808 event decomposition;
- full production/mastering profile;
- plug-in/processor inference;
- creative arrangement advice;
- Verse/Chorus/Bridge/Drop semantic naming;
- detailed motif/transcription analysis;
- AI-origin detection;
- ANN/million-track infrastructure;
- cloud/external integrations.

See [`FAR_TODO.md`](FAR_TODO.md) for promotion gates.
