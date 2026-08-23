# ARCHITECTURE

## v0.3 data flow

```text
Windows GUI / CLI
      |
      +----------------------- Analysis ------------------------+
      |                                                         |
      v                                                         v
file/folder input                                      Validation sources
      |                                              many roots / files
      v                                                         |
audio decode                                                   v
      |                                                SHA-256 track identity
      +--> BPM / key / spectral features                        |
      |                                                         v
      v                                                deduplicate by content
representative 30 s windows                                    |
      |                                                         v
      v                                              recheck filter / history
MAEST Discogs 519                                               |
      |                                                         v
      v                                              Fast / Auto / Accurate
raw style probabilities                              shared prediction cache
      |                                                         |
      +--> broad family aggregation                             v
      |                                                versioned AnalysisResult
      v                                                         |
genre resolver                                                  v
primary/hybrid/confidence                              SQLite history + snapshots
      |                                                         |
      +------------------------------+--------------------------+
                                     v
                              drift / convergence
                     JS divergence / cosine / Top-N overlap
                     BPM equivalence / key / label stability
                                     |
                                     v
                      STABLE / MINOR / SIGNIFICANT / CRITICAL
                                     |
                                     v
                           JSON / CSV / GUI reports
```

## Core modules

```text
analyzer.py          MAEST inference and shared multi-mode prediction cache
analysis_policy.py   Auto/Fast/Accurate window selection
resolver.py          human-facing genre resolution
track_identity.py    SHA-256 logical track identity
runtime_meta.py      schema/version/run/timestamp/git metadata
history.py           local SQLite persistence
comparison.py        pairwise result drift metrics and severity
convergence.py       Fast/Auto/Accurate convergence summary
validation_policy.py recheck-selection rules
validation.py        multi-root scan, recheck, version comparison
validation_gui.py    Validation Lab Tkinter tab
report.py            immutable run snapshots and validation reports
```

## History model

`track_id` is content-based, not path-based. Paths are locations of a track, not its identity.

SQLite stores:

```text
tracks
file_locations
runs
style_scores
broad_scores
validation_sessions
comparisons
```

The DB lives outside the repository by default and is ignored if a custom DB is placed inside the repo.

## Result immutability

A v0.3 run has a unique `run_id`. JSON snapshots include version/mode/run-id in the filename and therefore do not overwrite older run JSON.

Each run records analyzer/schema version, track identity, timestamps, model/revision, device, Git commit when available, window settings and both raw/resolved genre evidence.

## Multi-mode efficiency

When Validation requests `Fast + Auto + Accurate`, the audio is decoded once. A canonical duration-based window grid is created once, and predictions are cached by window index. Each mode then consumes the subset it needs.

This makes convergence testing substantially cheaper than launching three independent model pipelines.

## Design rules

- preserve raw classifier outputs separately from resolved human labels
- do not claim a single definitive genre when top broad families are nearly tied
- track identity must survive moves/renames and therefore uses content hashing
- history is append-oriented; old run snapshots are not silently overwritten
- GUI is a presentation/input layer; analysis/validation logic remains shared with CLI
- long ML work runs outside the Tk main thread
- comparisons measure stability, not objective correctness
- no model weights are stored in Git
- raw audio/video, generated `results/`, SQLite DBs and WAL/SHM files are ignored by Git
