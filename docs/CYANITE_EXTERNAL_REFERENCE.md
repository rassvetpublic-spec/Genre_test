# Cyanite external reference for Genre_test

Status: **external R&D reference / benchmark candidate; not production evidence**  
Snapshot date: **2026-08-30**  
Relevant areas: retrieval, descriptors, representative segments, structural segmentation, BPM/tempo validation

## Purpose

Cyanite is recorded here as an external commercial music-understanding system that can be used to benchmark and calibrate selected `Genre_test` research directions.

It must **not** become a required runtime dependency and its outputs must **not** silently overwrite MAEST, AudioSet AST, DSP, CLaMP, `AudioProfile`, or project-owned reviewed ground truth.

Recommended role:

```text
EXTERNAL_REFERENCE / BENCHMARK / TAXONOMY REFERENCE
```

Not:

```text
PRODUCTION_TRUTH / REQUIRED_ANALYZER / AUTOMATIC_RESOLVER_OVERRIDE
```

## Source set

### Primary public source — Cyanite Model Outputs

Official documentation:  
https://docs.cyanite.ai/docs/guides/model-outputs/

Verified on 2026-08-30.

The public API documentation lists versioned model outputs including:

- `BpmV2`;
- `CharacterV2`;
- `FreeGenreV3`;
- `InstrumentsV2`;
- `KeyV2`;
- `MainGenreV2`;
- `MoodAdvancedV2` / `MoodSimpleV2`;
- `MovementV2`;
- `MusicForV1`;
- `MusicalEraV2`;
- `RepresentativeSegmentV2`;
- `SegmentationV1`;
- `SubgenreV2`;
- `TempoV1`;
- `TimeSignatureV2`;
- `ValenceArousalV2`;
- `VocalsV2`;
- `VocalStyleV1`;
- `AutoDescriptionV2`;
- `AiMusicDetectionV1`.

The documentation also exposes track-level and, for several classifiers, segment-level score structures.

### Product update — Auto-Tagging 2.0

Official Cyanite product update, published 2026-08-27:  
https://cyanite.ai/blog/auto-tagging-2-0-product-update/

Relevant claims from Cyanite's own announcement:

- updated tagging models;
- new `Music For` use-case matching;
- new `Vocal Style` classification;
- new tempo model;
- updated BPM and instrument analysis;
- a new REST API for catalog-scale workflows;
- classifier analysis granularity increased to approximately 10-second intervals according to Cyanite's announcement.

These are vendor claims and must not be treated as independent scientific validation.

### User-provided Cyanite library reference

Workspace/library URL supplied for this project discussion:  
https://app.cyanite.ai/library/51852270

This URL may require authentication and is therefore recorded as a project reference, not as publicly reproducible evidence. Any track-specific conclusions taken from this library must be exported or manually recorded into project-owned benchmark fixtures before they can be cited as reproducible Genre_test evidence.

## Applicability to Genre_test

### 1. Retrieval benchmark

Strongest applicability: compare Cyanite search behavior with the local CLaMP 3 retrieval path.

Relevant `Genre_test` directions:

- audio-to-audio similarity;
- text-to-music retrieval;
- representative-segment search;
- reviewed relevance benchmark.

Preferred experiment:

```text
query track/text
  -> Genre_test / CLaMP Top-K
  -> Cyanite Top-K
  -> human reviewed relevance 0..3
  -> Precision@K / Recall@K / MRR / nDCG@K / overlap
```

Cyanite result overlap is an auxiliary comparison metric only. Human-reviewed project labels remain the benchmark truth source.

### 2. Descriptor calibration

Cyanite's public model taxonomy closely overlaps planned controlled descriptor experiments:

| Genre_test research area | Cyanite reference |
|---|---|
| mood / emotion | `MoodAdvancedV2`, `MoodSimpleV2`, `ValenceArousalV2` |
| character | `CharacterV2` |
| movement / groove | `MovementV2` |
| vocals | `VocalsV2`, `VocalStyleV1` |
| production / musical era | `MusicalEraV2` |
| instrumentation | `InstrumentsV2` |
| use-case descriptors | `MusicForV1` |
| generated description | `AutoDescriptionV2` |

Use Cyanite to inspect useful vocabulary design, disagreement cases, and candidate benchmark labels. Do not copy vendor scores into calibrated Genre_test confidence fields without project-owned validation.

### 3. Representative segment

`RepresentativeSegmentV2` provides a useful external comparator for Genre_test's deterministic centroid-based representative-segment selector.

Recommended reviewed fixture:

```text
track
  -> Genre_test representative interval
  -> Cyanite representative interval
  -> human preferred representative interval
```

Measure interval overlap and listening preference. Cyanite disagreement is not itself a failure.

### 4. Structural segmentation

`SegmentationV1` returns consecutive structural timeline sections without requiring Verse/Chorus semantic names. This is compatible with Genre_test's conservative structure-change philosophy.

Use it as an external comparator for:

- section/change boundaries;
- segment stability;
- representative section selection;
- structure UI research.

Do not infer Verse/Chorus/Bridge labels merely because a Cyanite section boundary exists.

### 5. BPM and tempo ambiguity

`BpmV2` and `TempoV1` are useful as external references when reviewing:

- half-time / double-time disagreement;
- tempo changes;
- difficult generated tracks;
- segment-level tempo behavior where exposed by the service.

Cyanite must not be treated as BPM ground truth. A disagreement such as `70 vs 140 BPM` should enter manual review or an independent fixture rather than automatically change the Genre_test result.

### 6. Vocal taxonomy reference

`VocalsV2` and `VocalStyleV1` are useful references for a minimal practical vocal taxonomy, including distinctions Cyanite documents such as vocal presence/style and categories including foreground/background, choir/a-cappella, sex/mixed classification and synthetic vocals.

This is particularly useful for evaluating the scope of future controlled vocal descriptors without prematurely implementing a large unsupported vocal inference surface.

## Explicit non-goals

- Do not require network access for normal `Genre_test` analysis or retrieval.
- Do not upload the whole local catalog to Cyanite as part of standard operation.
- Do not make Cyanite an authoritative genre resolver.
- Do not use Cyanite output to overwrite project evidence silently.
- Do not equate Cyanite `AiMusicDetectionV1` with project truth about origin, provenance, quality, or repair eligibility.
- Do not optimize audio processing to alter or evade Cyanite AI-origin detection scores.
- Do not call proprietary vendor output reproducible scientific ground truth.

## Evidence policy

For any future Cyanite-assisted experiment, retain at minimum:

- source track identity/hash where permitted;
- date of Cyanite analysis;
- Cyanite model/output version names;
- exported/raw result where terms permit;
- Genre_test build/backend identity;
- human review labels;
- comparison method and metrics;
- explicit distinction between vendor output and project-owned ground truth.

## Recommended priority

1. retrieval/search external benchmark;
2. descriptor taxonomy/calibration reference;
3. representative-segment comparison;
4. structural segmentation comparison;
5. BPM/tempo cross-check;
6. vocal taxonomy research;
7. generated descriptions/use-case tags as UX research only.

## Engineering conclusion

Cyanite is high-value for `Genre_test` as an **external control instrument** and taxonomy/UX reference. Its closest overlap is with v0.5 retrieval and descriptor research. The architecture should remain local-first and vendor-independent; Cyanite should stay outside the production evidence chain unless a future, explicitly scoped experiment proves a reason to change that boundary.
