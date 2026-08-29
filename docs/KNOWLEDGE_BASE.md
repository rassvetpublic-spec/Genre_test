# Genre_test engineering knowledge base

This document preserves durable engineering knowledge that is easy to lose when only the final implementation is documented. It complements `ACTIVE_CURRENT.md`, `ARCHITECTURE.md`, `GPU_RUNTIME.md`, `VALIDATION_LAB.md` and the roadmap.

It is **not** an install guide and it does not revive retired 0.3.x release procedures. Historical observations are retained only when they explain current invariants, regression requirements or future release-engineering decisions.

## Evidence rule

Knowledge recorded here must be one of:

- **Observed** — reproduced on real project input/runtime;
- **Derived** — a conservative conclusion directly supported by observed measurements;
- **Historical engineering lesson** — a failure mode already fixed, retained because the same class of bug can recur;
- **Calibration debt** — evidence exists, but it is not sufficient to claim a general ground truth.

Do not convert model output, filenames or one successful run into universal ground truth.

---

## 1. v0.4 Blackwell runtime acceptance evidence

### Observed

A real Windows smoke completed successfully on the target workstation with:

```text
Python: 3.12.10
PyTorch: 2.12.1+cu130
CUDA runtime: 13.0
GPU: NVIDIA GeForce RTX 5070 Ti
Compute capability: 12.0
Active architecture: sm_120
Compiled CUDA arch list: sm_75, sm_80, sm_86, sm_90, sm_100, sm_120
Blackwell native: true
```

`genre-test doctor` reported `Blackwell native (sm_120)`, not only `CUDA available=True`.

A real `--semantic on` analysis of `Бетховен - Симфония 5.mp3` then completed with both MAEST and the pinned AudioSet AST active. The run produced MAEST genre evidence plus AST instrumentation evidence (`Violin/fiddle`, `Orchestra`, `Bowed string instrument`, `Cello`) and did not fall back to MAEST-only mode.

### Derived invariant

For Blackwell, `torch.cuda.is_available()` is insufficient as a release gate. The active compute capability must be present in `torch.cuda.get_arch_list()`. A PTX/fallback-only success is not equivalent to the verified native runtime.

### Non-fatal warning observed

Transformers emitted:

```text
At least one mel filter has all zero values ... num_mel_filters (128) ... num_frequency_bins (257)
```

The warning did not interrupt AST initialization, inference or AudioProfile generation. It should not be silently suppressed merely to make logs clean; treat it as diagnostic debt until the preprocessing path is deliberately reviewed.

Canonical active runtime requirements remain in `GPU_RUNTIME.md`.

---

## 2. MAEST / AudioSet AST interpretation boundary

### Observed: classical corpus

A 25-track classical-music batch was analyzed with the MAEST-based v0.3.6 baseline. All 25 tracks resolved the **broad family** as `Classical`, often with high confidence.

That result is strong evidence that the broad Classical lane is useful. It is **not** evidence that MAEST fine labels inside `Classical---*` are reliable musicological period labels.

Representative mismatches from the batch:

| Work | MAEST-style result | Musicological interpretation / calibration target |
|---|---|---|
| Bach, Toccata and Fugue BWV 565 | Baroque | Baroque — aligned |
| Mozart Sonata / Turkish March | Classical | Classical — aligned |
| Brahms Hungarian Dances | Romantic | Romantic — aligned |
| Chopin Military Polonaise | Romantic | Romantic — aligned |
| Debussy `Pagodes` | Romantic | Impressionist vicinity |
| Debussy `The Girl with the Flaxen Hair` | Contemporary | Impressionist vicinity |
| Vivaldi `Autumn` | Romantic | Baroque |
| Paganini Capriccio | Baroque | early Romantic / Romantic vicinity |
| Prokofiev `Dance of the Knights` | Romantic | 20th-century / Modern vicinity |
| Ravel `Boléro` | Romantic | Modern / Impressionist vicinity |
| Wagner `Ride of the Valkyries` | Soundtrack | Romantic / Opera context |

### Derived invariant

`Classical---Romantic`, `Classical---Modern`, etc. are Discogs-style acoustic/style labels. They must not be presented as authoritative historical periods without a separately calibrated resolver.

The project should keep these concepts separate:

```text
Broad family: Classical
MAEST fine-style evidence: Romantic / Modern / Contemporary / ...
Optional calibrated classical period/style resolver: separate future layer
```

AudioSet AST helps with semantic/audio-event evidence such as instruments, orchestra, vocals and production character. It is not a historical-period classifier and must not be used as one.

### Regression asset to preserve

The 25-track corpus is useful as a future `CLASSICAL_25` reviewed fixture. The useful ground-truth columns are not only one `genre` field, but at least:

```text
expected_family
expected_period_or_style
acceptable_alternatives
expected_key where independently known
instrumentation where reviewed
```

The current roadmap already tracks classical resolver/calibration; this section records the evidence that motivated it.

---

## 3. Tempo-v2: short-loop 3:2 ambiguity and mastering robustness

### Observed failure mode

Two versions of the same short electronic/breakcore loop were analyzed:

```text
mylancore-bass_170bpm_F#_minor.wav
mylancore-bass_170bpm_F#_minor_ozone.wav
```

Both were approximately `22.588 s` long and both resolved `F# minor`. Before tempo-v2, the old single beat-tracker estimate produced:

```text
original: 110.29 BPM
Ozone:    117.19 BPM
```

The audio had not been time-stretched. The nearly identical durations rule out a real tempo change caused by ordinary Ozone filtering/mastering.

The old estimator was operating on the internal mono 16 kHz analysis stream and was attracted to a lower metric pulse near the `2/3` relationship of the intended fast grid. Mastering changed transient/spectral weighting enough to move the estimator between neighboring tempo hypotheses.

### Derived invariant

A mastering pass may change **tempo-detector evidence** without changing the actual musical tempo. Therefore:

- never infer a real tempo change from a single estimator jump after EQ/dynamics/mastering;
- compare duration/timebase first;
- preserve half/double and 3:2 candidates;
- use independently reviewed BPM fixtures before claiming calibration accuracy.

For this loop, the duration is also compatible with an approximately 64-beat, ~170 BPM grid, but the filename itself is not ground truth. It is a useful regression case, not a universal proof of the resolver.

---

## 4. Source audio metadata is not analysis-stream metadata

### Observed failure mode

The original and Ozone-rendered WAVs had different native container/PCM formats while the MAEST analysis stream was normalized internally.

Observed source properties:

```text
original: 44.1 kHz, 16-bit, stereo, PCM bitrate ~1411.2 kbps
Ozone:    48 kHz, 24-bit, stereo, PCM bitrate ~2304 kbps
```

The old architecture could accidentally expose properties derived after conversion to the internal 16 kHz analysis stream. That is semantically wrong even if classification itself is unaffected.

### Derived invariant

Keep two namespaces mentally and in code:

```text
SOURCE AUDIO
  container / codec / native sample rate / bit depth / channels / source bitrate

ANALYSIS STREAM
  decoder result / mono conversion / model sample rate / model windowing
```

User-facing source metadata must come from the original file/container probe, not from the MAEST/AST preprocessing stream.

---

## 5. Portable/bootstrap lessons retained for future release work

The old 0.3.6 portable line is retired. These are historical engineering lessons only, retained because v0.5+ will eventually need packaging again.

### 5.1 Isolated environments, shared download cache

A project should keep its own `.venv`. Reusing another project's venv, `PYTHONPATH`, or `--system-site-packages` creates dependency coupling.

Large wheels do not need to be downloaded from the network every time. The normal user `pip` cache can be shared across isolated environments. The correct optimization is:

```text
shared wheel/download cache
+
project-local isolated .venv
+
skip install when the existing runtime passes strict compatibility probes
```

### 5.2 Torch probe must distinguish warnings from failure

A real portable failure showed `torch=2.11.0+cu128 cuda=12.8 available=True` while stderr also contained a NumPy-related warning. Treating any stderr output as import failure was incorrect.

Robust probe pattern:

1. bootstrap required Python runtime packages such as NumPy before the first heavy-library probe when the library expects them;
2. run the probe in a separate process;
3. require exit code success;
4. require an explicit stdout success marker;
5. capture stderr separately for diagnostics;
6. do not let a warning alone determine success.

### 5.3 PowerShell stdout is part of a function's return value

A portable bootstrap failure occurred because a PowerShell function intended to return one executable path also emitted `pip install` stdout. PowerShell collected all emitted objects, so the caller received an array instead of one `System.String`, producing a parameter-transformation failure.

Durable rule:

```text
functions that return machine-consumed values must emit only those values
```

Human-facing command output should be routed explicitly to the host/log stream rather than accidentally becoming part of the function return pipeline.

### 5.4 GitHub Actions artifact ZIP is a wrapper

`actions/upload-artifact` exposes an artifact download as a ZIP archive. If the build product is itself a ZIP, users downloading the Actions artifact see `ZIP -> distribution ZIP` nesting.

For a user-facing portable package, publish the actual distribution ZIP as a release/repository asset or otherwise make the distinction explicit. Do not confuse the Actions transport wrapper with the product archive.

### 5.5 Do not move large release binaries through fragile text/base64 chat paths

A prior attempt to publish a release ZIP through a text/base64-oriented connector path produced a truncated binary. Release binaries should be copied/published by the build workflow or another binary-safe path, then verified with size, archive test and SHA-256.

### 5.6 Root launcher must not hardcode a retired release

The launcher previously contained a fixed `0.3.6` path/version assumption. The durable design is mode detection:

```text
Git working tree -> working-copy setup/runtime
packaged tree    -> release bootstrap/runtime
```

Version identity should come from project/package metadata, not a duplicated literal inside the launcher. A legacy bootstrap must not be selected for a newer release merely because the file happens to exist.

---

## 6. GUI/session boundary lesson

A batch-session log showed that the initial implementation captured `device`, analysis mode and presentation view at session start. Changing a combobox while the worker was already running therefore could not affect the active analyzer instance.

The safe live-switch boundary is the **track boundary**:

- changing Device or analysis mode must affect the next track, not migrate an inference already running on the current track;
- changing presentation/path options may be applied when rendering a completed result, but persistence semantics must stay explicit;
- Safe Stop remains authoritative over configuration changes.

Current product behavior is documented in `ACTIVE_CURRENT.md`; this section records why track-boundary semantics exist.

---

## 7. What was already present before this audit

The 2026-08-30 chat-to-repository audit found these items already represented in `main`, so they should not be re-added as competing documents:

- PyTorch 2.12.1 / CUDA 13.0 / native Blackwell runtime target;
- shared pip download cache with isolated `.venv`;
- `all` presentation view and Normal/SUNO/Distributor outputs;
- optional full source path;
- live Device/mode/view/path changes at safe boundaries;
- tempo-v2 half/double/3:2 handling;
- native source metadata separation;
- classical resolver/calibration as open work;
- MAEST + pinned AudioSet AST architecture;
- Ozone 12 consolidation under Genre_test and the frozen standalone OZONE12 repository boundary;
- retrieval/CLaMP 3 v0.5 direction and current roadmap.

The purpose of this knowledge base is to retain **why** these rules exist and the real observations behind them, not to duplicate active-state documentation.
