# Models

## Primary — MAEST Discogs 519

Default model id:

`mtg-upf/discogs-maest-30s-pw-129e-519l`

Purpose: fine-grained music style classification.

Runtime: Hugging Face Transformers + PyTorch.

Security/reproducibility note: the MAEST family can require `trust_remote_code=True`. For reproducible or controlled deployments, set an explicit model `revision` after reviewing the model repository.

## Not in MVP — musicnn

The original musicnn implementation uses TensorFlow 1.x. The available Keras port also targets very old TensorFlow. It is therefore deferred rather than made a hard dependency of the Windows MVP.

## Planned ensemble

Possible secondary channels:

1. a broad genre classifier;
2. zero-shot CLAP-style labels;
3. instrument/vocal/mood classifiers;
4. deterministic DSP features;
5. rule-based final resolver for distributor/Suno taxonomies.
