# Genre_test

**Current development version: 0.5.0.dev0**
**Published stable release: none; active development line: 0.5.0.dev0**

Genre_test is a local Windows-first music profiler and regression lab. Ordinary analysis combines **MAEST Discogs519 + pinned AudioSet AST + DSP** into an `AudioProfile`; Validation remains a dedicated reproducibility/drift workflow.

## Current analysis baseline

Ordinary analysis can produce all three views from one inference pass:

- **Normal** — genre, family, confidence, influences, semantic tags, source metadata, BPM/key and score evidence;
- **SUNO** — compact Style of Music handoff;
- **Distributor** — broad genre/subgenre-oriented mapping.

Default GUI/CLI view is `all`.

## Architecture

```text
Audio
  +--> MAEST Discogs519 fine-style evidence ----+
  +--> AudioSet AST semantic evidence ----------+--> deterministic fusion --> AudioProfile
  +--> DSP / source metadata -------------------+                           |
                                                                            +--> Normal
                                                                            +--> SUNO
                                                                            +--> Distributor

Raw MAEST evidence ---------------------------------------------------------> Validation
```

### Pinned models

MAEST:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
revision 6c35f32a350f74351870937d5ae0bae1d898d1df
```

AudioSet AST:

```text
MIT/ast-finetuned-audioset-10-10-0.4593
revision f826b80d28226b62986cc218e5cec390b1096902
```

Result schema: **4**.

## Runtime

Supported Windows runtime:

- **Python 3.13 x64 primary**; Python 3.12 x64 supported fallback; Python 3.11 is not supported;
- PyTorch 2.12.1;
- NVIDIA: CUDA 13.0 / cu130;
- Blackwell requires native active architecture; RTX 5070 Ti `sm_120` verified;
- CPU-only mode supported;
- FFmpeg required for extended decode fallback.

Runtime Health examples:

```text
GPU system: Runtime OK | Deps 12/12 | CUDA OK | GPU OK | FFmpeg OK | HF OK
CPU-only:   Runtime OK | Deps 12/12 | CUDA N/A | GPU N/A | FFmpeg OK | HF OK
```

If NVIDIA hardware exists but PyTorch CUDA is unusable, Runtime Health reports failure instead of silently treating the machine as CPU-only.

## Windows startup

### Git working copy

Clone/pull the repository and run:

```text
Genre_test_START.cmd
```

The launcher prepares/updates the private project `.venv`, prefers Python 3.13 x64, accepts Python 3.12 x64 as a fallback, and starts the GUI. If neither supported Python is available, first-run setup installs Python 3.13 x64.

`Genre_test_START.cmd` is the only supported user entry point for environment checks, dependency installation, optional retrieval runtime management and application startup. Scripts under `scripts/` are internal implementation details.

Working-copy retrieval commands:

```powershell
.\Genre_test_START.cmd retrieval-status
.\Genre_test_START.cmd retrieval-setup
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
```

During v0.5 development, `retrieval-setup` runs unattended. Model provenance remains documented; the distribution installer acceptance flow is deferred to v1.0.

### Portable packaging

No packaged stable release is currently published. The former portable release
has been retired from the active repository and from GitHub Releases/Tags.

Genre_test_START.cmd retains packaged-mode bootstrap support for a future
release, but there is no current release archive to download.

## GUI
The Runtime Health window has three tabs:

```text
Анализ | Validation | Проверка
```

### Анализ

- source file/folder selection;
- Device `auto/cpu/cuda` when CUDA is actually available;
- Auto / Fast / Accurate / Expert modes;
- Normal / SUNO / Distributor / all views;
- optional full source path;
- Expert MAEST window count and Top-K;
- Safe Stop;
- dark theme by default with live Dark / Light switch;
- clickable History/log locations.

Live mode/view/path/device changes are applied safely at track boundaries.

### Validation

Re-analyzes selected sources to measure convergence and history drift.

- Fast / Auto / Accurate or full Fast+Auto+Accurate comparison;
- all / stale-or-missing-build / unstable filters;
- explicit `DRIFT: STABLE/MINOR/SIGNIFICANT/CRITICAL` terminology;
- Safe Stop preserves completed results.

### Проверка

Compares saved builds without re-analyzing audio.

Build identity includes analyzer version + Git commit + schema + model revision. A preflight reports Build A coverage, Build B coverage and common tracks; 0-common-track comparisons are refused instead of emitting meaningless 0% metrics. Repeatability mode compares two runs of the same build.

## Analysis modes

| Mode | Behavior |
|---|---|
| Auto | default adaptive analysis; expands when evidence is ambiguous |
| Fast | up to 3 representative MAEST windows |
| Accurate | full duration-based target |
| Expert | manual window count and Top-K |

Duration target:

| Duration | Maximum MAEST windows |
|---:|---:|
| < 60 s | 1 |
| 60–120 s | 3 |
| 120–210 s | 5 |
| 210–300 s | 7 |
| 300–420 s | 9 |
| > 420 s | 11 |

## Input QC

```text
< 10 s   -> INSUFFICIENT_AUDIO, no genre verdict
10-30 s  -> SHORT_INPUT, one padded MAEST window, confidence <= medium
>= 30 s  -> NORMAL
```

## Tempo and source metadata

Tempo-v2 handles:

- normal BPM candidate;
- half/double-time relationships;
- short-loop 3:2 ambiguity.

The report exposes alternate tempo candidates, but stable repeated output is not treated as independent BPM ground truth.

Source sample rate, bit depth, channels and bitrate come from the original audio file and are not confused with the internal 16 kHz MAEST stream.

## History paths

Default working-copy runtime data:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\results\
```

History is gitignored. Historical JSON import remains available as a migration/data-recovery feature, but old portable release bootstrap semantics are not part of the active repository.

## CLI

Version and diagnostics:

```powershell
.\.venv\Scripts\genre-test.exe --version
.\.venv\Scripts\genre-test.exe doctor
```

Single file:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --view all
```

Recursive batch:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music" --device auto --mode auto --semantic auto --view all --full-path
```

Validation:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter all
.\.venv\Scripts\genre-test.exe validate "D:\Music" --compare-modes --filter all
```

Large repeatable regression:

```powershell
.\scripts\run_large_regression.ps1 -Source "D:\Music" -CompareModes
```

Omit `-CompareModes` for a faster Auto-only validation pass.

## Current development evidence

The core analysis/runtime baseline remains covered by Windows ensemble,
Validation, Safe Stop, CUDA/Blackwell, Ruff, pytest and PowerShell/runtime gates.
GitHub CI uses Python 3.13 for the full quality/runtime-contract gate and Python
3.12 for compatibility pytest. Documentation-only pull requests skip the heavy
Python setup/Ruff/full-pytest path but still run lightweight repository contract
tests on Python 3.13, and all required `test (...)` contexts fail closed if
preflight fails. `main` receives only a lightweight post-merge 3.13 smoke.
Those checks are development evidence and are not advertised as an active
packaged release.

## Integrated studio-finish direction
`Genre_test` is the single engineering source of truth for the wider AUDIO_MASTERING project. The former standalone `OZONE12_MASTERING_LAB` is being absorbed as the Ozone 12 mastering subsystem rather than maintained as a second product.

Canonical Ozone boundary:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

Ozone 12 Advanced remains an **optional mastering backend**. Ordinary analysis and retrieval must not require Ozone or REAPER. The full v0.7 path is planned as:

```text
Genre_test preflight
 -> mastering orchestration
 -> REAPER render host
 -> Ozone 12 Advanced
 -> WAV 24-bit / 48 kHz
 -> backend-neutral TechnicalProfile/QC
 -> A/B/X
 -> delivery
```

Ozone module order is treated as part of the sound. The imported 16-slot topology is an order template, not a default active chain; every processor must earn activation and `BYPASS` is a valid winner. Shared attack/mono/stereo/codec metrics are promoted into Genre_test common technical/QC code rather than duplicated inside the Ozone backend.

See [`docs/mastering/ozone12/README.md`](docs/mastering/ozone12/README.md), issue #100 and follow-up #101.

## Known development items

- shared audio decode/cache between MAEST and AST;
- persistent semantic cache;
- explicit fine-style ambiguity presentation for near-tied Top-1/Top-2 results;
- independent BPM ground-truth fixtures;
- classical resolver/calibration;
- larger reviewed benchmark/confusion analysis;
- similarity, XLSX and richer calibrated descriptors.

See [ROADMAP.md](ROADMAP.md) and [docs/ACTIVE_CURRENT.md](docs/ACTIVE_CURRENT.md).
