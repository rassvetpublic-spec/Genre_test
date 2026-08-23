# Architecture v0.1

## Pipeline

```text
Audio file
  -> decode/resample mono 16 kHz
  -> full-track deterministic features
  -> representative 30 s windows
  -> MAEST Discogs519 classification per window
  -> mean aggregation
  -> broad genre hierarchy
  -> JSON / CSV report
```

## Why MAEST first

MVP intentionally avoids `musicnn` because its original runtime is tied to TensorFlow 1.x, and common Keras ports are tied to very old TensorFlow. MAEST is exposed through current Hugging Face Transformers and gives a much richer Discogs-style taxonomy.

## Window strategy

A full song can change style between intro/verse/chorus/bridge. One arbitrary 30-second crop is fragile, therefore the default is five uniformly spaced windows. Scores are averaged across windows.

Later versions should support:

- energy-aware window selection;
- chorus/section detection;
- separate intro/verse/chorus genre estimates;
- multi-model calibration.

## Interpretation

`primary_genre` is the highest aggregate broad family inferred from hierarchical labels. `top_styles` keeps finer labels. The tool must not pretend that a probabilistic classifier supplies an objective genre truth.
