# Genre_test SUPERCOMBINE TODO

Parent epic: #49

This checklist describes work **after and around v0.5**. It must not silently turn the v0.5 CLaMP milestone into an unbounded release.

Long-term target:

```text
Generated song
  -> analyze / catalog / search
  -> technical QC and markers
  -> separate stems when needed
  -> repair artifacts
  -> repair vocals
  -> repair/post-process stems
  -> recombine / mix
  -> master / delivery normalization
  -> synchronized A/B/X review
  -> metadata/tag audit
  -> final export + manifest
```

The objective is studio-ready audio with audible generative defects corrected. The project does not optimize audio for detector evasion or provenance concealment.

---

## Foundation shared by all future phases

- [x] v0.4 stable analyzer/history/Validation baseline
- [x] v0.5 CLaMP retrieval architecture started (#26)
- [x] Geekatplay `music-suite` fork created
- [x] Geekatplay `ComfyUI-MusicMapper-nodes` fork created
- [x] Geekatplay org reuse audit documented
- [x] live Resource Monitor implemented in PR #42 (#48)
- [ ] complete `TechnicalProfileOutputV1` (#45)
- [ ] implement `GenerativeDefectProfileV1` from `docs/GENERATIVE_DEFECT_PROFILE.md`
- [ ] validate corpus manifest/annotation schemas from `docs/GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`
- [x] capture ranked GitHub/Reddit evidence in `docs/GENERATIVE_AUDIO_REPAIR_SOURCE_REGISTRY.md`
- [x] audit top-10 upstream terms, weights, runtime and maintenance in `docs/GENERATIVE_AUDIO_REPAIR_TOP10_AUDIT.md`
- [ ] recheck the pinned-revision audit before any backend graduates from experimental
- [ ] build private-local 50–100 excerpt corpus; target v1 = 80 real SUNO excerpts plus clean controls
- [ ] freeze pilot/calibration/test/challenge splits by parent source
- [ ] establish two-reviewer annotation and disagreement/adjudication protocol
- [ ] shared decode/canonical stereo buffer
- [ ] timestamped technical marker contract
- [ ] common `ProcessingManifest` / `DerivedAssetIdentity` contract
- [ ] common Safe / Probe / Refine variant naming
- [ ] parent/source hash lineage for every derived render
- [ ] common before/after metric snapshot
- [ ] common error/unknown/fallback semantics

---

# v0.6 — Repair & Stem Lab

## #50 Generative artifact remediation

- [ ] define curated artifact taxonomy
- [ ] define timestamped artifact marker schema
- [ ] collect real generated-song fixtures
- [ ] create audible-artifact review protocol
- [ ] spectral discontinuity detector
- [ ] localized clipping/click detector
- [ ] unstable harsh/high-frequency texture detector
- [ ] phase/mono instability detector
- [ ] transient-smear diagnostic
- [x] candidate restoration backend inventory (`docs/GENERATIVE_AUDIO_REPAIR_SOURCE_REGISTRY.md`)
- [ ] deterministic DSP Safe/Probe baselines
- [ ] A2SB bandwidth-extension/local-inpainting spike
- [ ] compare Apollo vs A2SB vs DSP vs stem-assisted routes by defect class
- [ ] clean-control over-processing and false-positive gates
- [ ] Apollo compatibility/provenance/runtime spike (#63)
- [ ] pin Apollo code revision, checkpoint identity, license and SHA-256
- [ ] verify whether Timbrica MP3/Vocal/Universal variants map to public reproducible checkpoints
- [ ] define optional isolated `ApolloRepairBackend` / sidecar contract
- [ ] add source eligibility gate: lossy/suspected transcode vs clean lossless default-skip
- [ ] create R0 Original / R1 Light / R2 Vocal Light / R3 Standard / R4 Aggressive Probe matrix
- [ ] add `ROBUSTNESS AXIS: SOURCE_RESTORATION` for MAEST/AST/BPM/key/CLaMP comparisons
- [ ] keep restoration-induced differences separate from analyzer-build `DRIFT`
- [ ] benchmark real Windows Python 3.12 + Torch cu130 + RTX 5070 Ti sm_120
- [ ] require immutable source, derived identity and processing manifest for Apollo outputs
- [ ] backend license/provenance audit
- [ ] Safe repair pass
- [ ] Probe variants
- [ ] bounded Refine loop
- [ ] delta/null render
- [ ] loudness-matched before/after
- [ ] marker reduction + damage guard
- [ ] processing manifest
- [ ] hidden/randomized loudness-matched listening sessions via #54
- [ ] report artifact reduction and musical damage as separate outcomes
- [ ] allow `FULL_MIX_WINS`, `REGENERATE_SOURCE` and `INCONCLUSIVE` verdicts
- [ ] CPU/GPU benchmark

Explicit non-goals:

- AI-detector score minimization;
- watermark/provenance stripping;
- origin concealment.

## #51 Vocal repair processor

- [ ] `VocalRepairBackend` protocol
- [ ] vocal-stem input identity
- [ ] vocal-specific TechnicalProfile markers
- [ ] pitch stability diagnostic
- [ ] sustained-note confidence model/estimator evaluation
- [ ] sibilance/resonance map
- [ ] breath/noise balance diagnostics
- [ ] phrase-level level consistency
- [ ] clipped/smeared consonant/transient detection
- [ ] dereverb backend research
- [ ] de-noise backend research
- [ ] dedicated vocal restoration model research
- [ ] conventional DSP fallback chain
- [ ] Safe / Probe / Refine renders
- [ ] loudness-matched vocal A/B
- [ ] final vocal-vs-mix context check
- [ ] preserve unprocessed stem

### Vocal intelligence candidates

- [ ] maintained transcription backend evaluation
- [ ] Russian lyrics transcription accuracy benchmark
- [ ] supplied-lyrics vs rendered-vocal alignment
- [ ] phrase/word timestamps
- [ ] pronunciation/diction QA experiment
- [ ] melody/pitch-event backend evaluation (Basic Pitch-like candidate or maintained alternative)
- [ ] keep vocal identity/timbre manipulation separate from ordinary repair

## #52 Stem repair/post-processing

- [ ] `StemProcessorBackend` protocol
- [ ] maintained source-separation backend matrix
- [ ] torchaudio/Open-Unmix-style candidate evaluation
- [ ] separation quality fixture set
- [ ] vocals/drums/bass/other stem identity
- [ ] per-stem TechnicalProfile
- [ ] separation bleed/artifact detector
- [ ] drums transient recovery
- [ ] drum harshness/resonance cleanup
- [ ] bass/sub cleanup
- [ ] bass mono/phase stabilization
- [ ] instrumental stem denoise/de-harsh
- [ ] vocal handoff to #51
- [ ] stem latency/phase alignment validation
- [ ] recombination integrity check
- [ ] full-mix delta report
- [ ] optional stem-aware structure geometry

---

# v0.7 — Studio Finish / Mastering Orchestration

The default mastering direction remains compatible with the separate OZONE12_MASTERING_LAB philosophy: staged, measurable processing with REAPER as host and Ozone module order treated as critical. Genre_test should orchestrate/evaluate renders rather than pretend a simplistic internal chain replaces Ozone.

## Mastering orchestration

- [ ] versioned mastering request/manifest contract
- [ ] source technical preflight
- [ ] delivery target profiles
- [ ] Spotify / Apple Music / YouTube / Yandex / VK profile research
- [ ] target LUFS / True Peak policy separated from artistic loudness goal
- [ ] render backend abstraction
- [ ] REAPER render-host bridge
- [ ] Ozone preset/XML bridge boundary
- [ ] stage progress / heartbeat / cancel
- [ ] Safe / Probe / Refine candidate generation
- [ ] bounded refinement loop
- [ ] post-render TechnicalProfile self-check
- [ ] codec-preview validation
- [ ] mono-loss check
- [ ] decoded codec peaks
- [ ] drum-attack retention metric
- [ ] reject/regenerate candidate on hard technical failure

## #54 Synchronized A/B/X comparison lab

- [ ] 2–12 candidate session model
- [ ] common playhead
- [ ] synchronized seek/loop
- [ ] per-candidate mute/solo
- [ ] loudness-match toggle
- [ ] blind A/B/X mode
- [ ] instant candidate switching
- [ ] waveform overlays
- [ ] marker overlays
- [ ] delta/null render where valid
- [ ] technical summary cards
- [ ] timestamp notes
- [ ] score dimensions: vocal/drums/bass/tonal/width/artifacts/loudness/preference
- [ ] candidate settings/render manifest view
- [ ] selected-winner persistence
- [ ] comparison report export

## Interactive technical review

Inspired by Music Suite:

- [ ] marker-aware waveform
- [ ] jump to next/previous issue
- [ ] selected-region loop
- [ ] spectrum view
- [ ] stereo/vector view
- [ ] spectrogram view
- [ ] selected-region TechnicalProfile
- [ ] source vs candidate overlay

---

# v0.8 — Metadata, Catalog & Delivery Operations

## #53 Media tag auditor / batch fix

### Read/normalize

- [ ] `ffprobe` + `mutagen` merge adapter
- [ ] MP3/ID3
- [ ] FLAC/Vorbis comments
- [ ] M4A/MP4 atoms
- [ ] OGG support validation
- [ ] raw unknown-tag preservation
- [ ] title/artist/album artist/album
- [ ] track/disc
- [ ] genre
- [ ] date/year
- [ ] composer
- [ ] comment/description
- [ ] lyrics inventory
- [ ] BPM
- [ ] key
- [ ] language
- [ ] publisher/copyright/ISRC
- [ ] embedded artwork inventory

### Analyzer cross-check

- [ ] tag BPM vs tempo-v2
- [ ] tag key vs analyzed key/mode
- [ ] tag genre vs resolved genre/family
- [ ] missing metadata report
- [ ] conflicting aliases report
- [ ] invalid track/disc/date checks
- [ ] confidence-aware correction suggestions
- [ ] identity fields never auto-overwritten

### Batch mutation safety

- [ ] full dry-run diff
- [ ] no destructive selection by default
- [ ] original tag backup manifest
- [ ] atomic temp write
- [ ] post-write re-read
- [ ] hash/audio-payload preservation check where feasible
- [ ] rollback command/UI
- [ ] batch summary CSV/JSON
- [ ] tag-only operation avoids audio transcode where container allows

## #56 Local music asset vault

- [ ] index source/stems/repairs/masters/reports
- [ ] role classification
- [ ] parent/derived lineage graph
- [ ] file hash/integrity state
- [ ] analyzer build/model provenance
- [ ] processing manifest links
- [ ] tag audit state
- [ ] CLaMP index state
- [ ] selected comparison winner
- [ ] lexical FTS
- [ ] semantic search reason display
- [ ] similarity floor
- [ ] duplicate/near-duplicate groups
- [ ] storage footprint by role/root
- [ ] cleanup candidates
- [ ] recoverable trash/quarantine
- [ ] explicit `MEASURED / FILE METADATA / MODEL INFERENCE / USER ENTERED / DERIVED` badges

## Delivery package

- [ ] WAV 24-bit/48 kHz canonical master export
- [ ] alternate delivery formats
- [ ] checksum manifest
- [ ] analysis summary
- [ ] TechnicalProfile report
- [ ] processing lineage
- [ ] tag report
- [ ] final cover-art association metadata
- [ ] distributor-ready checklist

---

# v0.9 — ComfyUI / Runtime / Automation

## #46 Genre_test ComfyUI bridge

- [ ] Analyze node
- [ ] Profile To Text node
- [ ] Core Sound node
- [ ] Search Text node
- [ ] Search Audio node
- [ ] Similar Tracks node
- [ ] Retrieval Status node
- [ ] TechnicalProfile node
- [ ] Repair request/status nodes
- [ ] candidate comparison session export/import

## #55 ModelRuntimeManager / VRAM scheduler

- [ ] backend residency registry
- [ ] model fingerprint
- [ ] acquire/release lifecycle
- [ ] exclusive/coexistence groups
- [ ] conservative/balanced/keep-warm modes
- [ ] Resource Monitor telemetry integration
- [ ] observed VRAM high-water mark
- [ ] idle unload
- [ ] pre-heavy-stage unload
- [ ] sidecar shutdown
- [ ] CUDA cache lifecycle
- [ ] CPU fallback
- [ ] OOM retry policy
- [ ] stress sequence MAEST+AST -> CLaMP -> separation -> repair

## Automation/API

- [ ] stable local job API
- [ ] processing progress/heartbeat contract
- [ ] safe stop/cancel
- [ ] local-only authentication decision
- [ ] optional MCP facade after stable APIs exist
- [ ] workflow validation before execution
- [ ] no arbitrary third-party script execution

---

# v1.0 — SUPERCOMBINE graduation

One project/session must be able to move through:

```text
INGEST
 -> ANALYZE
 -> SEARCH/REFERENCE
 -> QC
 -> STEMS (optional)
 -> REPAIR
 -> VOCAL/STEM POST
 -> MIX/MASTER
 -> A/B/X REVIEW
 -> TAG AUDIT
 -> DELIVERY
```

## v1.0 acceptance

- [ ] source remains immutable
- [ ] every derived asset has lineage and processing manifest
- [ ] resumable session survives restart
- [ ] heavy backends are optional and independently diagnosable
- [ ] resource monitor works through full pipeline
- [ ] all destructive operations have preview + recovery
- [ ] automatic repair has confidence/unknown semantics
- [ ] final technical QC gate
- [ ] synchronized listening review available
- [ ] tag audit complete
- [ ] 24-bit/48 kHz master export
- [ ] Russian documentation complete
- [ ] representative real SUNO-song end-to-end fixtures
- [ ] benchmark performance on RTX 5070 Ti / sm_120
- [ ] licenses/provenance explicit
- [ ] no anti-detector-evasion objective
- [ ] explicit MTD

---

# Broad TODO discovered from GeekatplayStudio org

Keep these visible even before dedicated issues exist:

- [ ] result `match reason` transparency for semantic/catalog search
- [ ] similarity floor so search can return zero good results
- [ ] integrity verdict for every source and derived asset
- [ ] safe staged model/runtime downloads with SHA-256
- [ ] quarantine corrupted downloads
- [ ] free-space preflight before large model/render operations
- [ ] storage footprint dashboard
- [ ] processing/render dependency graph
- [ ] safe staged self-update architecture
- [ ] waveform + marker review ergonomics
- [ ] selected-region analysis
- [ ] lyrics transcription/alignment
- [ ] melody/pitch-event extraction
- [ ] stem-aware section similarity graph
- [ ] 3D song geometry visualization (optional/FAR)
- [ ] automatic playlist/recommendation graph after retrieval benchmark
- [ ] local MCP/agent automation interface after contracts stabilize
- [ ] report exports: JSON/CSV/HTML/PDF as appropriate
- [ ] delivery-readiness summary cards
- [ ] EBU/compliance optional backend
- [ ] noisereduce/restoration preview research
- [ ] retained human-readable processing history

No item becomes default merely because an upstream project contains it. Promotion still requires licensing, fixtures, repeatability and a clear failure path.
