# ARCHITECTURE — v0.4.0

## Product data flow

```text
file / folder input
      |
      +--> native source metadata --------------------------+
      +--> DSP: BPM / key / features ----------------------+ 
      +--> MAEST Discogs519 -------------------------------+--> AudioProfile fusion
      |      fine styles / broad families                  |        |
      +--> AudioSet AST -----------------------------------+        +--> Normal
             semantic genre/vocal/instrument/mood                   +--> SUNO
                                                                    +--> Distributor

raw MAEST evidence --> history / Validation / build comparison
```

## Core analysis modules

```text
profile_analyzer.py       ordinary MAEST + AST orchestration
analyzer.py               MAEST inference and mode-aware window cache
semantic_analyzer.py      pinned AudioSet AST inference
profile.py                AudioProfile evidence fusion / family reconciliation
analysis_policy.py        Auto/Fast/Accurate window selection
resolver.py               raw MAEST fine-style resolver
features.py               tempo/key/DSP features
source_metadata.py        original file metadata
presentation.py           Normal/SUNO/Distributor text views
```

## Validation / history modules

```text
track_identity.py         SHA-256 logical track identity
runtime_meta.py           schema/version/run/timestamp/git metadata
history.py                local SQLite persistence
build_history.py          composite saved-build identity
comparison.py             pairwise result drift metrics
convergence.py            Fast/Auto/Accurate convergence summary
validation_policy.py      recheck-selection rules
validation.py             multi-root scan, recheck and comparison
validation_gui.py         Validation GUI
check_gui.py              saved-build comparison GUI
```

## Build identity

Analyzer semver alone is not sufficient during development. A saved build is identified by the relevant combination of:

```text
analyzer_version
git_commit
schema_version
model_id
model_revision
```

This prevents different `0.4.0` commits from being treated as one build.

## History model

`track_id` is content-based, not path-based. Paths are locations of a logical track.

SQLite stores analysis runs and evidence append-only. New runs do not silently overwrite previous runs.

Default working-copy history:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
```

## Multi-mode efficiency

Validation Fast + Auto + Accurate uses one decoded track and a shared MAEST window-prediction cache. Each mode consumes the window subset it needs.

Ordinary semantic analysis is currently a separate decode/inference path. Shared MAEST/AST decode/cache is planned for v0.4.1.

## Runtime architecture

Working copy:

```text
Genre_test_START.cmd
  -> scripts/setup.ps1
  -> project .venv
  -> Runtime Health
  -> GUI
```

Packaged release:

```text
Genre_test_START.cmd
  -> scripts/release_bootstrap.ps1
  -> project-local .venv
  -> doctor/runtime gates
  -> GUI
```

Current supported release runtime is Python 3.11-3.13 + PyTorch 2.12.1, with CUDA 13.0/cu130 on NVIDIA and CPU PyTorch otherwise.

## Design rules

- preserve raw classifier evidence separately from presentation labels
- final published Genre and Family must be internally consistent
- weak semantic evidence must not be promoted to full source confidence by normalization
- track identity survives moves/renames through content hashing
- history is append-oriented
- GUI is presentation/input; analysis logic remains shared with CLI
- long ML work stays outside the Tk main thread
- Safe Stop is cooperative and preserves completed work
- comparisons measure stability, not objective correctness
- no model weights or raw audio are stored in Git
- generated `results/`, SQLite DBs and runtime caches are gitignored
