# GeekatplayStudio org audit for Genre_test SUPERCOMBINE

Audit date: 2026-08-26

Purpose: identify reusable architecture, algorithms and UX patterns from public `GeekatplayStudio/*` repositories that can strengthen the Genre_test long-term studio-finish supercombine.

This document is an **architecture/reuse audit**, not permission to copy code blindly. Every reused implementation still requires a per-repository license/provenance check and a pinned upstream commit.

## Product boundary

Long-term target:

```text
Generated mix / stems
  -> analyze
  -> catalog/search
  -> technical QC + markers
  -> repair
  -> vocal/stem post-processing
  -> mix/master orchestration
  -> synchronized candidate comparison
  -> metadata/tag audit
  -> final delivery package
```

Goal wording: remove audible defects, unstable synthetic artifacts and weak mix/master characteristics of raw generative songs so the result reaches a studio-ready standard. The project does **not** optimize audio to evade AI-origin/provenance detectors.

---

## 1. `GeekatplayStudio/music-suite`

Pinned audit snapshot:

```text
8534963ccafa37dc23df84c6ac239132fba77d41
```

Status: preferred reusable upstream where license allows. Existing fork: `rassvetpublic-spec/music-suite`.

### High-value components

#### Technical QC / marker engine
Already identified for #45:

- Integrated LUFS and loudness timeline;
- sample peak / oversampled true peak;
- crest factor;
- clipping segments;
- stereo correlation / Mid-Side / L-R balance timelines;
- spectral balance;
- harshness, sibilance, sub-bass and mono-compatibility markers;
- timestamped problem regions.

Adopt selectively behind versioned `TechnicalProfileOutputV1`; do not replace stable Genre_test genre/tempo logic.

#### Metadata extraction
`audioqi/io/metadata.py` combines `ffprobe` and `mutagen`, normalizes common aliases and keeps unknown/raw tags available. Useful basis for #53.

Important fields already modeled upstream include:

- title / artist / album artist / album;
- track / disc;
- genre;
- date/year;
- composer/comment/lyrics;
- BPM / key;
- language / publisher / copyright / ISRC.

Genre_test extension: compare these values against analyzer evidence, generate a dry-run change manifest, preserve original raw tags and support post-write re-read validation + rollback.

#### Mastering orchestration patterns
`audioqi/mastering.py` contains useful architecture even though Genre_test should not copy its internal DSP as the final mastering engine:

- explicit presets and delivery profiles;
- source-aware preflight adaptation;
- bounded refinement passes;
- optional reference input;
- multiple optional mastering backends;
- iterative LUFS/true-peak targeting;
- post-master self-check / repair pass;
- persistent status/progress/manifest;
- output candidate records.

Reuse the **orchestration and validation pattern**, while REAPER/Ozone and future repair backends remain separate processors.

#### Interactive review UI
Current functionality includes waveform/spectrum/stereo/spectrogram views, timeline playback, marker-aware zoom and focused segment review.

Candidate for post-v0.5 GUI:

- waveform timeline with markers;
- jump-to-problem;
- selected-region analysis;
- before/after overlay;
- codec preview and delivery-readiness panel.

#### Optional separation/restoration research
Upstream notes explicitly recommend additive/feature-flagged evaluation of:

- Essentia;
- noisereduce;
- Open-Unmix / torchaudio-based separation;
- Basic Pitch;
- pyebur128.

They also note that the original Demucs repository is archived; treat it as research/reference rather than the default new dependency.

---

## 2. `GeekatplayStudio/song-geometry-mapper`

Pinned audit snapshot:

```text
ebb1032519488fee0ecfe55e684442e542cb9211
```

### High-value components

The project models a song as time-indexed frames with descriptors and temporal/similarity edges.

Per-frame features include:

- RMS;
- ZCR;
- spectral centroid;
- spectral spread;
- rolloff;
- flatness;
- peak frequency;
- spectral flux.

Useful mapping/structure ideas:

- temporal edges;
- kNN similarity edges;
- PCA/manifold projection;
- time-spine representation;
- hybrid chronology + similarity layout;
- optional stem-focused geometry;
- smoothing/normalization policies.

### Genre_test use

Do not make 3D visualization a v0.5 dependency. Reuse the underlying concepts for:

- #33 representative segments;
- #44 structure/change-point map;
- beat-switch detection;
- stem-specific anomaly localization;
- future catalog/track geometry visualization;
- similarity-of-sections graph.

Potential future output:

```text
section nodes = CLaMP segment embedding + DSP frame statistics
edges = chronological + semantic similarity
```

---

## 3. `GeekatplayStudio/Ai-Music-Analytic-Mastering-Nodes`

Pinned audit snapshot:

```text
7923bda9bba66d8ace2020464d89f1c8ee3386ec
```

GitHub currently reports no repository license. Treat code as **reference only** until licensing is resolved.

### High-value concept: Global Model Cache

`nodes.py` keeps only one heavy audio model active, explicitly drops the old reference, runs Python GC and clears CUDA cache before loading another model.

This directly motivates #55 `ModelRuntimeManager`.

Genre_test needs a more rigorous version:

- model/backend fingerprint;
- acquire/release lifecycle;
- exclusive/coexistence groups;
- observed VRAM telemetry;
- idle-unload and keep-warm modes;
- sidecar shutdown hooks;
- OOM recovery;
- Resource Monitor (#48) integration;
- no unloading while a stage is executing.

### Other ideas worth keeping in TODO

- smart resampling/level matching when combining tracks;
- model-specific prompt adapters as a future creative layer;
- explicit workflow validation before running a model chain;
- memory-aware switching between heavy audio models.

Do **not** adopt the simplified `tanh`/RMS auto-mastering path as our mastering baseline.

---

## 4. `GeekatplayStudio/ABCvers-Studio`

Pinned audit snapshot:

```text
a52e0d38facd3ad00bf6c6cfdb0c64ac82c8dd12
```

README declares MIT.

### High-value concept: synchronized comparison

ABCvers can drive up to twelve media panels with one transport and synchronized position/zoom.

Adapt to audio as #54:

- source + multiple masters/repairs in one session;
- common playhead and loop;
- instant A/B/X switching;
- loudness-match toggle;
- blind comparison mode;
- per-candidate mute/solo;
- annotations at timestamps;
- settings/render manifest beside each candidate;
- waveform/marker overlays;
- technical metrics and null/delta comparison.

This is especially valuable for Ozone Safe/Probe/Refine decisions.

---

## 5. `GeekatplayStudio/ComfyUI-Asset-Vault`

Pinned audit snapshot:

```text
c950ed1b7b91099b6ef3b663e7cf0468f744a38d
```

### High-value product patterns

#### Local inventory and lineage
Adapt into #56:

- index source, stems, repair renders, masters and reports;
- `derived_from` graph;
- processing/model/build fingerprints;
- integrity/readability verdict;
- storage footprint;
- selected-winner relationship;
- index/search state.

#### Truth/provenance labels
A particularly strong UX rule: do not present guesses as measurements.

Genre_test should standardize visible field provenance:

```text
MEASURED
FILE METADATA
MODEL INFERENCE
USER ENTERED
DERIVED / PROCESSING MANIFEST
```

#### Search
Asset Vault combines always-available lexical FTS with optional semantic search and exposes why a result matched.

Genre_test already plans CLaMP semantic search; borrow the transparency rule:

- show `semantic`, `metadata`, `genre`, `BPM`, etc. as match reasons;
- enforce similarity floor instead of always returning the least-unrelated tracks.

#### Safe operations
Excellent patterns to reuse for any destructive/batch workflow:

- show full action plan before mutation;
- nothing selected by default for destructive actions;
- check free space first;
- checksum downloaded artifacts;
- quarantine on mismatch;
- never execute third-party install scripts automatically;
- recoverable trash / rollback;
- staged updates applied before application startup;
- archive path/traversal/size safety limits.

These principles should also govern #53 batch tag editing and future repair-render cleanup.

---

## 6. `GeekatplayStudio/ComfyUI-LipSync-GAP` and `video-indexing-ai`

Useful only as architectural references for now.

Both contain Whisper-related transcription/audio-feature paths.

Possible future use:

- lyrics transcription;
- word/phrase timestamps;
- vocal problem localization by lyric phrase;
- compare supplied lyrics against rendered vocal;
- pronunciation/diction QA;
- synchronized lyric display in A/B lab.

Do not vendor their Whisper implementation. Evaluate a maintained, licensed transcription backend separately.

---

## 7. Additional TODO candidates from the org audit

### High-value / likely future issues

- shared heavy-model runtime/VRAM scheduler (#55);
- synchronized A/B/X listening lab (#54);
- reversible tag auditor/batch fixer (#53);
- local music asset vault / lineage / integrity (#56);
- vocal repair (#51);
- stem repair (#52);
- generative artifact restoration (#50).

### Keep in broad TODO until evidence/backend selection

- lyrics transcription + alignment;
- melody/pitch-event extraction;
- stem-aware structure geometry;
- interactive marker-aware waveform/spectrogram review;
- stricter EBU/delivery compliance backend;
- optional noise/restoration preview;
- local MCP/automation API for external tools;
- semantic result explanation / match reasons;
- catalog storage/cleanup analysis;
- safe staged self-update architecture;
- delivery preset/export matrix;
- project lineage graph and reproducible render manifests.

### FAR / optional presentation

- 3D song geometry visualization;
- music-driven video generation bridges;
- social-media asset packaging;
- automatic creative prompt rewriting.

---

## Reuse rules

1. Pin upstream commit before copying/adapting code.
2. Verify repository and dependency licenses.
3. Prefer architecture/algorithm reuse over wholesale vendoring.
4. Keep optional heavy models isolated.
5. Preserve v0.4/v0.5 analysis truth contracts.
6. A repair/mastering result must carry a manifest and parent/source identity.
7. Every destructive batch action needs dry-run + rollback.
8. Never optimize for bypassing AI-origin/provenance detection.
9. No merge to `main` without explicit MTD.
