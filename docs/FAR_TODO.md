# Genre_test — FAR TODO

This document stores useful ideas that are **not part of the current v0.5 release contract**.

Rule: an item can move from FAR TODO into an active issue only when we can name a reproducible signal/model, version its identity, define validation data, and state how failure is represented. Attractive prose alone is not enough.

## 1. Rich vocal profile

Desired outputs:

- spoken language;
- diction/articulation clarity;
- vocal presence probability;
- lead/background separation;
- singing / rap / spoken / voiceover;
- register (low/mid/high);
- timbre descriptors (raspy, breathy, bright, dark, etc.);
- delivery descriptors (conversational, aggressive, intimate, restrained, etc.);
- dry/wet estimate;
- close/distant estimate;
- center/wide vocal position.

Why FAR:

- AudioSet/CLaMP tags alone are not sufficient evidence for all of these claims;
- language/diction needs speech-aware evidence;
- register/timbre requires a calibrated vocal model or carefully reviewed estimator;
- spatial position needs DSP/source-separation evidence and is mix-dependent.

Near-term exception: #37 may experimentally evaluate a **small controlled vocal vocabulary** through CLaMP zero-shot scores, but those scores do not become production facts until calibrated.

## 2. Detailed rhythm / drum / bass profile

Desired outputs:

- kick/snare/clap/hat activity;
- hi-hat roll density;
- syncopation;
- off-grid / loose timing;
- groove strength;
- 808/sub-bass presence;
- sliding bass character;
- drum transient density;
- main beat vs secondary groove;
- pattern descriptors such as Jersey Club / halftime / doubletime behavior.

Why FAR:

- some high-level movement/groove descriptors can be tested in #37;
- reliable event-level claims require beat/onset/source-aware analysis, not only semantic embeddings.

A future promotion path should combine beat tracking + onset statistics + optional source separation + reviewed rhythmic fixtures.

## 3. Full production / mix profile

Desired outputs:

- polished/raw production character;
- stereo width;
- center stability;
- mono compatibility;
- transient punch;
- saturation character;
- macro/micro dynamics;
- tonal brightness/darkness;
- vocal depth;
- reverb/dryness;
- loudness/true peak/crest-factor style metrics.

Why FAR:

- objective DSP metrics and perceptual descriptors must remain separate;
- terms such as `pristine`, `raw`, `punchy`, `wide`, `tube-like` need calibration before publication.

Some objective mastering-oriented measurements may later be shared with OZONE12_MASTERING_LAB, but Genre_test must keep model identity and measurement definitions explicit.

## 4. Processing-character inference

Potential user-facing wording:

```text
Likely processing character:
  hard-clipping-like
  saturation-heavy
  transient-enhanced
```

Hard rule:

- never claim a specific plug-in, brand, model, or processing chain from rendered audio unless metadata actually provides it;
- `analog tube saturation`, `hard clipper`, etc. may only be presented as **perceptual processing character**, not as known production history.

Why FAR:

- requires reviewed examples and careful false-positive analysis.

## 5. Creative advice / arrangement suggestions

Examples:

- suggest a beat switch;
- suggest tempo lift;
- suggest drop/bridge contrast;
- suggest instrumentation or transition FX;
- generate SUNO-oriented production advice.

Why FAR:

- this is recommendation/generation, not audio measurement;
- it must never be mixed into factual analysis output.

Future architecture should expose two explicit modes:

```text
Analysis only
Analysis + Creative recommendations
```

The recommendation layer should consume structured analysis and remain separately versioned.

## 6. Production era / stylistic decade

Desired output:

```text
Production era: 2020s
Confidence: medium
```

Important definition: predicted sonic/production era, **not release year**.

Near-term exception: #37 may benchmark a controlled decade vocabulary. It remains experimental until manually calibrated.

## 7. Instrument / motif decomposition

Desired outputs:

- main harmonic motif;
- riff/hook type;
- piano/guitar/synth prominence;
- orchestral/electronic layers;
- foreground/background instrumentation;
- motif direction such as ascending/descending when reliably measurable.

Why FAR:

- AST tags are useful but insufficient for detailed motif claims;
- richer output may require source separation, pitch tracking, transcription, or dedicated music encoders.

## 8. Section labels and full arrangement semantics

Potential labels:

- intro / verse / pre-chorus / chorus / bridge / drop / breakdown / outro;
- beat switch;
- silence/mute;
- build/riser;
- tape-stop-like transition;
- density/energy change.

Near-term subset: #44 will implement **change-point / tempo-map infrastructure** without pretending that every segment can already be named Verse/Chorus correctly.

Full semantic section naming remains FAR until benchmarked.

## 9. Audio generation / AI-origin detection

Potential future subsystem:

- AI-generated likelihood;
- supported-generator fingerprints;
- model/version/provenance;
- unknown/unsupported state.

Why FAR:

- detectors decay rapidly as generators change;
- false-positive risk is high;
- must be an independent model output, never a hidden profile heuristic.

## 10. Large-catalog advanced retrieval

Only after exact cosine on current catalog is measured:

- FAISS/HNSW/USearch;
- million-track indexing;
- cluster map / UMAP-like visual exploration;
- automatic playlists;
- catalog dedup / near-duplicate grouping;
- recommendation graphs.

Current ~10k catalog does not justify ANN complexity yet.

## 11. External integrations

Deferred:

- Spotify/playlist matching;
- distributor APIs;
- cloud catalog ingestion;
- public web API;
- S3/object storage;
- multi-user server mode.

Genre_test remains local-first until retrieval quality and local catalog UX are proven.

## Promotion gate from FAR TODO

Before promoting any item:

1. identify data/model source;
2. verify license/provenance;
3. define versioned output schema;
4. define confidence/unknown semantics;
5. create reviewed fixtures;
6. measure precision/repeatability;
7. add regression tests;
8. document failure modes;
9. create dedicated `realise` issue;
10. do not merge without MTD.
