# Genre_test — FAR TODO

This document stores useful ideas that are **not part of the current v0.5 release contract**.

Rule: an item can move from FAR TODO into an active issue only when we can name a reproducible signal/model, version its identity, define validation data, and state how failure is represented. Attractive prose alone is not enough.

Long-term execution work that has already been promoted beyond v0.5 is tracked in [`SUPERCOMBINE_TODO.md`](SUPERCOMBINE_TODO.md) under epic #49.

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

Near-term exception: #37 may experimentally evaluate a **small controlled vocal vocabulary** through CLaMP zero-shot scores. Separate future #51 handles **vocal repair processing**, not publication of this full descriptive profile.

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

## 3. Full perceptual production / mix profile

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

Why partly FAR:

- objective DSP metrics are being promoted separately through #45 TechnicalProfile;
- perceptual labels such as `pristine`, `raw`, `punchy`, `wide`, `tube-like` still require calibration before publication.

Objective mastering-oriented measurements may later be shared with OZONE12_MASTERING_LAB, but Genre_test must keep model identity and measurement definitions explicit.

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

## 9. AI-origin detection / provenance QA

Potential future independent subsystem:

- AI-generated likelihood;
- supported-generator fingerprints;
- model/version/provenance;
- unknown/unsupported state;
- false-positive/false-negative benchmark.

Why FAR:

- detectors decay rapidly as generators change;
- false-positive risk is high;
- it must be an independent model output, never a hidden profile heuristic.

Hard boundary:

- detection may be used for provenance/audit research;
- Genre_test does not optimize mastering/repair to lower detector scores;
- no detector-evasion, provenance-stripping or watermark-removal objective.

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

## 12. Lyrics transcription, alignment and pronunciation QA

Geekatplay repositories such as `ComfyUI-LipSync-GAP` and `video-indexing-ai` contain Whisper-related architecture that makes this direction worth keeping visible.

Potential outputs:

- transcription text;
- word/phrase timestamps;
- supplied lyrics vs rendered lyrics diff;
- missing/repeated line detection;
- pronunciation/diction problem timestamps;
- lyric-synchronized A/B review.

Why FAR:

- do not vendor their Whisper implementation blindly;
- choose a maintained licensed transcription backend;
- singing transcription accuracy, especially Russian, needs its own benchmark.

Parts may later support #51 vocal repair after validation.

## 13. Melody / pitch-event extraction

Potential uses:

- vocal pitch stability diagnostics;
- melody contour;
- wrong sustained-note candidate detection;
- note/pitch overlays;
- motif comparison;
- supplied reference melody alignment.

Candidate family to evaluate later: Basic Pitch-like models or a more suitable maintained alternative.

Why FAR:

- model/backend has not been selected;
- polyphonic and expressive singing failure modes need reviewed fixtures;
- this must not become automatic pitch correction without confidence gates.

## 14. 3D song geometry / structure visualization

Inspired by Geekatplay `song-geometry-mapper`.

Possible view:

```text
node = segment/frame
position = DSP + embedding geometry
edge = chronological or semantic similarity
```

Could visualize:

- structure changes;
- similar/repeated sections;
- stem-specific trajectories;
- unusual/outlier regions;
- catalog clusters.

Why FAR:

- useful presentation/research tool but not required to improve audio quality;
- underlying structure features should ship before 3D presentation.

## 15. Local MCP / agent automation interface

Both Music Suite and Asset Vault demonstrate local MCP/API patterns.

Possible future controls:

- analyze file/folder;
- query catalog;
- start index job;
- run technical QC;
- request repair/master candidate;
- inspect job state;
- open comparison session;
- generate delivery report.

Why FAR:

- internal CLI/job contracts should stabilize first;
- external automation must not gain implicit destructive file-write authority.

## 16. Music-to-video / social release package

Geekatplay has music/video and social-media tooling that could eventually sit after final audio delivery.

Potential scope:

- waveform/visualizer video;
- lyric video timing export;
- short preview clips;
- cover-art association;
- platform asset bundle.

Why FAR:

- downstream presentation is not part of core audio finishing;
- keep v1.0 audio pipeline focused before broadening into campaign tooling.

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
