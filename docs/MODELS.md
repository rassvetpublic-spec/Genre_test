# Models — v0.4.0

## MAEST Discogs519

Primary fine-style classifier:

```text
model: mtg-upf/discogs-maest-30s-pw-129e-519l
revision: 6c35f32a350f74351870937d5ae0bae1d898d1df
```

Purpose:

- detailed genre/style evidence;
- broad-family aggregation;
- Fast / Auto / Accurate / Expert analysis modes;
- raw evidence used by Validation.

Runtime: Hugging Face Transformers + PyTorch.

## AudioSet AST

Independent semantic classifier:

```text
model: MIT/ast-finetuned-audioset-10-10-0.4593
revision: f826b80d28226b62986cc218e5cec390b1096902
```

Purpose:

- independent semantic genre evidence;
- vocal tags;
- instrumentation;
- mood/production evidence.

AST does not replace MAEST fine-style classification. Its mapped family contribution preserves absolute confidence so a lone weak semantic tag cannot receive the full semantic vote after normalization.

## Evidence fusion

Ordinary `AudioProfile` combines MAEST, AST and DSP/source metadata deterministically.

Rules include:

- protect high-confidence MAEST decisions;
- reduce confidence on model disagreement;
- keep final Genre and Family internally consistent;
- preserve raw model evidence in stored results;
- allow MAEST-only fallback when semantic mode is `auto` and AST is unavailable.

## Runtime

Both learned models use the same supported PyTorch runtime:

- PyTorch 2.12.1;
- NVIDIA CUDA 13.0 / cu130;
- native Blackwell architecture required when applicable;
- CPU-only PyTorch supported.

## Future models

Any additional model must provide genuinely useful independent evidence and integrate reproducibly with the supported Windows/Python/PyTorch environment. Obsolete TensorFlow-1-era/musicnn runtime paths are not part of the active architecture.
