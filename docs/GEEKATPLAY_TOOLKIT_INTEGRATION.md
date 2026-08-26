# Geekatplay Toolkit Integration Plan

Status: **candidate upstream toolkit for Genre_test v0.5+**  
Related issues: **#45, #46, #47**

## Upstreams inspected

### 1. GeekatplayStudio/music-suite

Pinned snapshot:

```text
repo:   GeekatplayStudio/music-suite
commit: 8534963ccafa37dc23df84c6ac239132fba77d41
license: MIT
```

Music Suite is the preferred source for reusable technical-analysis ideas/code because it has an explicit MIT license and a broader, more mature local-first architecture.

Relevant upstream areas:

```text
audioqi/core/analyzer.py
audioqi/core/metrics.py
audioqi/core/markers.py
audioqi/core/music_style.py
audioqi/geometry_mapper/features.py
audioqi/geometry_mapper/analyze.py
audioqi/integrations/comfyui/sonic_holodeck/
apps/mcp/
```

Observed capabilities relevant to Genre_test:

- integrated loudness / loudness timelines;
- sample peak and oversampled true peak;
- crest factor and approximate LRA;
- stereo timelines/correlation;
- mono-compatibility markers;
- clipping segments;
- noise-floor estimate;
- spectral balance / spectrum curve;
- sibilance, harshness-band and sub-bass timelines;
- marker-first output tied to time ranges;
- frame-wise spectral geometry;
- optional Demucs stem analysis;
- local Ollama descriptions kept beside a deterministic measured report;
- local MCP integration;
- bundled ComfyUI integration.

### 2. GeekatplayStudio/ComfyUI-MusicMapper-nodes

Pinned snapshot:

```text
repo:   GeekatplayStudio/ComfyUI-MusicMapper-nodes
commit: 0fda892fddfbaf50ba384c34f2b2d73c68d64208
license metadata: null
root LICENSE: not found during inspection
```

This repository is valuable primarily as a ComfyUI integration reference and a small audio-analysis sandbox.

Observed useful patterns:

- ComfyUI native `AUDIO` input/output;
- explicit audio path handling;
- spectrogram generation/reconstruction workflows;
- DSP extraction with librosa;
- Krumhansl-Schmuckler style key estimate;
- librosa tempo baseline;
- LAION-CLAP demonstration;
- human-readable/Suno-style output;
- optional local Ollama path.

Important limitation: the inspected LAION-CLAP path compares the track against a small hard-coded candidate list and softmaxes only those candidates. That is not a general genre classifier and its softmax must not be interpreted as calibrated genre confidence.

Because explicit software licensing was not found, do not copy substantial source from this standalone repository into Genre_test until licensing is clarified. Forking/tracking it as an upstream reference is separate from relicensing or vendoring its code.

## Integration decision

Genre_test will **not** become a fork of Music Suite and will not merge either upstream application wholesale.

Instead:

```text
Geekatplay upstreams
      |
      +--> measured algorithms / integration patterns
      |
      v
Genre_test-owned versioned contracts
      |
      +-- Analysis / AudioProfile (existing)
      +-- Retrieval / CLaMP 3 (v0.5)
      +-- TechnicalProfileOutputV1 (#45)
      +-- Segment / structure outputs (#33/#44)
      +-- ComfyUI thin bridge (#46)
```

This keeps Genre_test's reproducibility, build history and Validation model intact.

## What to promote first

### A. TechnicalProfileOutputV1 — #45

High-value objective fields:

```text
loudness.integrated_lufs
loudness.lra
peaks.sample_peak_dbfs
peaks.true_peak_dbfs
dynamics.crest_factor_db
stereo.correlation_timeline
stereo.mono_compatibility
clipping.segments
noise_floor_dbfs
spectral.balance
spectral.harshness_timeline
spectral.sub_bass_timeline
spectral.sibilance_timeline
markers[]
```

Every field must record algorithm identity/version and units.

Do not import subjective adjectives such as `pristine`, `raw`, `tube-like`, `punchy` as facts merely because technical metrics exist.

### B. Geometry/structure candidate — #33/#44

Music Suite frame descriptors are a useful deterministic companion to CLaMP segments:

```text
RMS
spectral centroid
spectral bandwidth/spread
spectral rolloff
spectral flatness
zero-crossing rate
peak frequency
```

Potential uses:

- structural change-point features;
- repeat/similarity visualization;
- tempo-map boundary support;
- catalog map diagnostics;
- explanation layer for why neighboring frames differ.

CLaMP embeddings remain the semantic retrieval representation; simple spectral geometry is not a replacement for them.

### C. Deterministic description — #43

The Music Suite pattern is directly compatible with Genre_test policy:

```text
measured/versioned features
        -> deterministic rule-based description
        -> optional local LLM description shown separately
```

Genre_test baseline remains deterministic. An optional Ollama enhancement, if later added, must never replace or overwrite the measured description.

### D. ComfyUI bridge — #46

Preferred architecture:

```text
ComfyUI AUDIO / path
      |
      v
Genre_test bridge node
      |
      +--> installed Genre_test CLI/local service
      |
      v
versioned JSON result
```

Do not maintain separate MAEST/AST/CLaMP model copies inside ComfyUI by default.

Initial nodes:

```text
GenreTest Analyze
GenreTest Profile To Text
GenreTest Core Sound
GenreTest Search Text
GenreTest Search Audio
GenreTest Similar Tracks
GenreTest Retrieval Status
```

## What not to adopt blindly

### MusicMapper hard-coded CLAP labels

Useful for demonstrations/zero-shot experiments only. Genre_test uses CLaMP 3 shared embeddings for retrieval and MAEST+AST for the stable genre profile.

### RMS/ZCR/centroid prose as factual production history

Threshold-based descriptions can be useful presentation hints, but they are not proof of exact instrumentation, mastering chain, plug-in type or artistic intent.

### Spectrogram `lossless` claim

The phase-aware STFT image idea is interesting, but any image serialization/quantization path must be independently measured before Genre_test calls reconstruction lossless.

### Whole Music Suite mastering chain

Genre_test is not a mastering application. Objective technical metrics may be shared with OZONE12_MASTERING_LAB, while render/mastering control remains in the mastering project.

## Fork/provenance policy — #47

Preferred forks:

```text
rassvetpublic-spec/music-suite
rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

Rules:

- preserve complete upstream history;
- document the upstream remote;
- pin upstream SHA for every integration batch;
- preserve MIT notice where Music Suite code is copied/substantially reused;
- do not vendor/relicense standalone MusicMapper source while license remains unclear;
- Genre_test never depends on an unpinned moving fork `main`.

## Cross-project value

The Music Suite technical-analysis layer is also relevant to `OZONE12_MASTERING_LAB`:

- true peak;
- loudness/LRA/crest;
- mono compatibility;
- stereo correlation;
- harshness/sibilance/sub-bass markers;
- before/after regression guards.

Do not couple the repositories yet. First stabilize a shared metric definition or small standalone package/API contract, then decide whether Genre_test and Ozone consume the same implementation.

## Immediate execution order

1. create/pin forks (#47);
2. finish CLaMP runtime foundation (#27/#29);
3. map Music Suite DSP against existing Genre_test/Ozone metrics (#45);
4. create `TechnicalProfileOutputV1` contract and tests;
5. connect selected frame features to segment/change-point work (#33/#44);
6. implement Genre_test ComfyUI thin bridge (#46);
7. only then consider optional Ollama/visual/MCP extensions.
