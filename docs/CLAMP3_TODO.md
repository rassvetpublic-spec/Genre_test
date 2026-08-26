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
- [ ] build modern isolated Windows runtime on the target machine
- [ ] audio embedding smoke
- [ ] Russian text embedding smoke
- [ ] measure repeatability
- [ ] measure cold/warm latency
- [ ] measure VRAM/RAM
- [ ] test after MAEST+AST CUDA usage
- [ ] test core-native compatibility
- [ ] write final runtime decision

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
- [ ] add serialization round-trip helpers
- [ ] finalize retrieval SQLite schema
- [ ] add schema version/migration tests
- [ ] define sidecar protocol version
- [ ] define structured error codes

### #29 Real CLaMP+MERT backend
- [ ] MERT adapter
- [x] exact upstream-compatible preprocessing v1 pinned in runtime manifest
- [ ] CLaMP audio adapter
- [ ] CLaMP multilingual text adapter
- [ ] subprocess handshake
- [ ] binary/NPY vector transport
- [ ] lazy loading
- [ ] clean shutdown / GPU release
- [ ] missing model / OOM / decode errors
- [ ] repeatability evidence

### #30 Cache/index
- [ ] retrieval.sqlite3
- [ ] track embedding persistence
- [ ] vector SHA-256
- [ ] stale backend detection
- [ ] atomic vector writes
- [ ] cache hit/miss metrics
- [ ] exact dense matrix index
- [ ] stable cosine ranking
- [ ] incremental update
- [ ] rebuild/stale-only commands

## P1 — product retrieval

### #31 Audio similarity
- [ ] full-track query
- [ ] self-match sanity
- [ ] Top-K exact ranking
- [ ] family/genre filters
- [ ] BPM filter
- [ ] key policy/filter
- [ ] confidence filter
- [ ] vocal/mood/instrument/production filters
- [ ] JSON/CSV export

### #32 Russian text search
- [ ] RU UTF-8 text embedding
- [ ] native RU baseline without LLM rewrite
- [ ] text Top-K search
- [ ] paired RU/EN benchmark
- [ ] query history
- [ ] empty/oversized query handling

### #33 Segments
- [ ] segment policy benchmark
- [ ] 30 s baseline windows
- [ ] segment persistence
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
- [ ] retrieval-doctor
- [ ] index
- [ ] index-status
- [ ] search-text
- [ ] search-audio
- [ ] reindex --stale-only
- [ ] stable exit codes
- [ ] Cyrillic path/query tests

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
- [ ] reuse v0.4 track_id/profile metadata
- [ ] embed only retrieval layer
- [ ] resume/safe-stop
- [ ] >=99% coverage or explained failures
- [ ] second-pass cache verification
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
