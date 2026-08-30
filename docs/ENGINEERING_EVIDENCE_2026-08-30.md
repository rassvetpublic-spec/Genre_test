# Engineering evidence retained from historical project/chat work — 2026-08-30

Status: **historical evidence / regression rationale, not current-state authority**
Issue: **#135**
Supersedes the useful evidence content of stale PR #133.

## Authority boundary

This document preserves observations and failure modes that explain why current Genre_test rules exist. It is deliberately **not** a second knowledge plane and does not override:

- `AGENTS.md`;
- `docs/ACTIVE_CURRENT.md`;
- `docs/ARCHITECTURE.md`;
- `ROADMAP.md`;
- subsystem contracts;
- Research Radar canonical JSON / generated Obsidian projections;
- live GitHub Issue/PR state.

If a current contract differs from a historical statement below, the current contract wins. The durable value here is the observation, regression rationale or engineering failure mode.

Evidence classes:

- **OBSERVED** — reproduced on real project input/runtime;
- **DERIVED INVARIANT** — conservative conclusion directly supported by an observation;
- **HISTORICAL FAILURE MODE** — fixed bug retained as regression rationale;
- **CALIBRATION DEBT** — useful evidence that is insufficient for universal ground truth.

## 1. Blackwell runtime + MAEST/AST acceptance

### OBSERVED

A real Windows target-workstation smoke completed with:

```text
Python: 3.12.10
PyTorch: 2.12.1+cu130
CUDA runtime: 13.0
GPU: NVIDIA GeForce RTX 5070 Ti
compute capability: 12.0
active architecture: sm_120
Blackwell native: true
```

`genre-test doctor` reported native `sm_120`, not merely `CUDA available=True`.

A real semantic analysis of `Бетховен - Симфония 5.mp3` then ran with both MAEST and the pinned AudioSet AST active. The run produced MAEST genre evidence plus AST instrumentation evidence including orchestra/bowed-string classes and did not fall back to MAEST-only mode.

### DERIVED INVARIANT

For Blackwell acceptance, `torch.cuda.is_available()` alone is insufficient. The active compute capability must be represented by the installed Torch build. PTX/fallback-only execution is not equivalent to the verified native runtime.

### CALIBRATION DEBT

Transformers emitted the warning:

```text
At least one mel filter has all zero values ... num_mel_filters (128) ... num_frequency_bins (257)
```

The warning did not prevent AST initialization, inference or AudioProfile generation. It should remain diagnostic evidence rather than being treated as an automatic runtime failure or silently suppressed without a deliberate preprocessing review.

Current runtime requirements remain owned by the active GPU/runtime documentation and code/tests.

## 2. Classical-25 evidence and label boundary

### OBSERVED

A reviewed 25-track classical batch analyzed with the MAEST-based baseline resolved the broad family as `Classical` for all 25 tracks, often with high confidence.

Representative fine-label behavior included both aligned and historically misleading cases:

| Work | MAEST-style result | Musicological interpretation / calibration target |
|---|---|---|
| Bach, Toccata and Fugue BWV 565 | Baroque | Baroque — aligned |
| Mozart Sonata / Turkish March | Classical | Classical — aligned |
| Brahms Hungarian Dances | Romantic | Romantic — aligned |
| Chopin Military Polonaise | Romantic | Romantic — aligned |
| Debussy `Pagodes` | Romantic | Impressionist vicinity |
| Debussy `The Girl with the Flaxen Hair` | Contemporary | Impressionist vicinity |
| Vivaldi `Autumn` | Romantic | Baroque |
| Paganini Capriccio | Baroque | early-Romantic / Romantic vicinity |
| Prokofiev `Dance of the Knights` | Romantic | 20th-century / Modern vicinity |
| Ravel `Boléro` | Romantic | Modern / Impressionist vicinity |
| Wagner `Ride of the Valkyries` | Soundtrack | Romantic / Opera context |

### DERIVED INVARIANT

Discogs/MAEST fine-style labels such as `Classical---Romantic`, `Classical---Modern` or `Classical---Contemporary` must not be presented as authoritative musicological period labels without separately calibrated evidence.

Keep the concepts distinct:

```text
broad family: Classical
MAEST fine-style evidence: model/style vocabulary
musicological period/style: separate reviewed/calibrated layer if implemented
```

AudioSet AST provides semantic/audio-event evidence and is not a historical-period classifier.

### FOLLOW-UP FIXTURE SHAPE

The historical batch is useful as a future reviewed `CLASSICAL_25` regression fixture if source rights/identity are preserved outside Git as appropriate. Useful reviewed fields include:

```text
expected_family
expected_period_or_style
acceptable_alternatives
expected_key where independently known
instrumentation where reviewed
```

This is fixture rationale, not a claim that all 25 labels constitute immutable scientific ground truth.

## 3. 170-BPM short-loop / Ozone tempo ambiguity

### OBSERVED

Two approximately `22.588 s` versions of the same short electronic/breakcore loop were analyzed:

```text
mylancore-bass_170bpm_F#_minor.wav
mylancore-bass_170bpm_F#_minor_ozone.wav
```

Both resolved `F# minor`. Before tempo-v2, the older single-estimator path returned approximately:

```text
original: 110.29 BPM
Ozone:    117.19 BPM
```

The material had not been time-stretched and durations remained essentially equal. Ordinary mastering changed transient/spectral weighting enough to move the estimator between neighboring metric hypotheses.

### DERIVED INVARIANT

A mastering pass can change **tempo-detector evidence** without changing actual musical tempo. Therefore:

- do not infer real tempo change from one estimator jump after EQ/dynamics/mastering;
- compare duration/timebase first;
- retain half/double and 3:2 ambiguity candidates where supported;
- use independently reviewed BPM fixtures before claiming calibration accuracy.

The filename's `170bpm` token is supporting context, not ground truth by itself.

## 4. Source metadata vs internal analysis stream

### OBSERVED

The original and Ozone-rendered WAVs in the tempo case had different native PCM properties while the model analysis path used normalized internal preprocessing.

Observed source properties included:

```text
original: 44.1 kHz, 16-bit, stereo, PCM bitrate ~1411.2 kbps
Ozone:    48 kHz, 24-bit, stereo, PCM bitrate ~2304 kbps
```

### DERIVED INVARIANT

Keep source/container metadata separate from model-analysis preprocessing:

```text
SOURCE AUDIO
  container / codec / native sample rate / bit depth / channels / source bitrate

ANALYSIS STREAM
  decoder result / channel conversion / model sample rate / model windowing
```

User-facing source metadata must come from the original source/container probe rather than from a resampled/mono model stream.

## 5. Release/bootstrap failure modes worth retaining

The old portable release line is retired. These lessons remain useful because the same failure classes can recur.

### 5.1 Shared cache is not shared environment

Correct pattern:

```text
shared wheel/download cache
+
project-local isolated .venv
+
skip install when strict compatibility probes pass
```

Reusing another project's venv, `PYTHONPATH` or `--system-site-packages` couples otherwise independent environments.

### 5.2 Probe warnings are not failures

A real runtime probe emitted non-fatal warning text on stderr while the tested Torch runtime itself was usable.

Robust probe pattern:

1. bootstrap prerequisite runtime packages when required;
2. execute the probe in a separate process;
3. require successful exit code;
4. require an explicit machine-readable stdout success marker;
5. capture stderr separately for diagnostics;
6. do not classify any warning text as failure by itself.

### 5.3 PowerShell stdout contaminates function return values

### HISTORICAL FAILURE MODE

A PowerShell function intended to return one executable path also emitted command stdout. PowerShell collected all emitted objects, so the caller received an array rather than one string and later parameter binding failed.

Durable rule:

```text
functions returning machine-consumed values must emit only those values
```

Human-facing output should be routed explicitly to host/log channels.

### 5.4 GitHub Actions artifact ZIP is a transport wrapper

`actions/upload-artifact` downloads as a ZIP archive. If the product is itself a ZIP, users see `artifact ZIP -> product ZIP` nesting. Do not confuse the transport wrapper with the distribution artifact.

### 5.5 Binary release artifacts require binary-safe transport

A historical text/base64-oriented publication attempt produced a truncated release archive. Large binaries should be moved by binary-safe build/release tooling and verified with archive test, size and SHA-256.

### 5.6 Root launcher must not hardcode a retired release

A root launcher previously carried a fixed old-version path assumption. Durable selection is by installation context and package metadata rather than duplicated version literals:

```text
Git working tree -> working-copy setup/runtime
packaged tree    -> release bootstrap/runtime
```

## 6. GUI/session live-switch boundary

### OBSERVED

An early batch worker captured device, analysis mode and presentation settings at session start. Editing a combobox while inference was already running could not safely migrate the active analyzer.

### DERIVED INVARIANT

The safe boundary for analysis/device changes is the **track boundary**:

- a device or analysis-mode change affects the next track;
- it does not mutate inference already running for the current track;
- presentation/path changes may be applied to completed-result rendering when the current UI contract permits it;
- Safe Stop remains authoritative over configuration changes.

Current GUI behavior remains owned by active product documentation/code; this section only preserves the rationale.

## 7. Transfer status

This ledger intentionally preserves only evidence/rationale that was at risk of remaining in stale PR #133 or historical chat context. Current product facts already represented elsewhere are not duplicated here as authority.

After this evidence is merged, stale PR #133 can be closed as superseded without losing its project-relevant unique observations.
