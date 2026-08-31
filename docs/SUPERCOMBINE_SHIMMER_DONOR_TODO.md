# SUPERCOMBINE Shimmer donor migration TODO

Tracking: **#160**
Parent epic: **#49**
Architecture: `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`

This file turns the authorized Shimmer donor and the owner-supplied development history into an actionable Genre_test migration backlog.

## P0 — donor/provenance freeze

- [x] owner authorization recorded in #160;
- [x] owner confirms licensing is not a blocker and authorizes copy/modify/integration/redistribution for the new Genre_test project;
- [x] public donor baseline pinned to `ff8344ae1a77bd7eb5be46b55c83813e923d3d2c`;
- [x] direct donor code limited to recoverable/pinned source;
- [x] changelog-only local additions classified as requirements/TODO until exact source is supplied and pinned;
- [x] `SHIMMER_EXTERNAL_REFERENCE.md` reclassified as authorized donor source;
- [x] workstation UI architecture documented;
- [x] Ozone Universal Core duplicate checked by SHA-256;
- [x] Anti-AI detector-evasion objective explicitly excluded;
- [x] common transport dependency placed before Repair/Stems/Master candidate surfaces;
- [ ] merge P0 after exact-head CI/review.

## P1 — workstation shell

### Donor UI extraction

Use only files present in the pinned/recoverable donor source for direct PORT/ADAPT work.

- [ ] inventory public `static/index.html` sections and split into Genre_test views;
- [ ] inventory reusable public CSS tokens/layout/components;
- [ ] extract/adapt topbar/sidebar/workspace/statusbar patterns where recoverable;
- [ ] remove Shimmer branding from migrated UI surface;
- [ ] introduce Genre_test workstation identity and version display;
- [ ] define web asset namespace under Genre_test source tree;
- [ ] keep existing desktop GUI as fallback during migration.

### Navigation

- [ ] Project;
- [ ] Analyze;
- [ ] Catalog;
- [ ] Search;
- [ ] Repair;
- [ ] Stems;
- [ ] Master;
- [ ] Compare;
- [ ] Delivery;
- [ ] Settings.

### RU/EN i18n

The owner changelog describes a broad local `static/js/i18n.js` implementation, but that exact local source is not pinned. Treat its behavior as a requirement, not directly portable code, unless source is later supplied.

- [ ] implement/adapt a Genre_test-owned i18n core;
- [ ] RU default remains configurable;
- [ ] EN complete fallback;
- [ ] no mixed hardcoded UI strings in new workstation modules;
- [ ] persist language in project/user settings;
- [ ] tests for missing translation keys.

### Local API shell

- [ ] select minimal local web framework only after compatibility review;
- [ ] `/health` / runtime status contract;
- [ ] project/session endpoints;
- [ ] job start/status/cancel contract;
- [ ] structured errors;
- [ ] no heavy model imports in web process at module import time;
- [ ] localhost-only default binding;
- [ ] graceful absence of optional backends.

### Minimal runtime HUD adapter

P1 includes only the shell-level adapter required by #164:

- [ ] consume existing Genre_test Resource Monitor/runtime truth;
- [ ] compact GPU/VRAM/CPU/RAM status presentation;
- [ ] explicit N/A for unsupported telemetry;
- [ ] no donor duplicate polling backend.

## P2 — current Genre_test capabilities in workstation

### Analyze

- [ ] submit source to existing analysis service;
- [ ] show AudioProfile without redefining semantics;
- [ ] TechnicalProfile/QC cards;
- [ ] timestamped marker view;
- [ ] explicit `MEASURED / FILE METADATA / MODEL INFERENCE / USER ENTERED / DERIVED` badges;
- [ ] progress + Safe Stop;
- [ ] export current reports.

### Catalog

- [ ] roots and indexed/stale/missing/failed counts;
- [ ] incremental index actions;
- [ ] backend/model identity;
- [ ] no hidden model download;
- [ ] preserve completed embeddings on Safe Stop.

### Search

- [ ] text query;
- [ ] audio-file query;
- [ ] selected-track query;
- [ ] full/representative/custom-segment scope;
- [ ] filters;
- [ ] top-K + similarity + match reason;
- [ ] zero-good-result behavior through similarity floor.

## P3 — common transport, preview and comparison

This is the shared #54-compatible foundation required before Repair/Stems/Master candidate UI. Do not create a private repair-only player.

The owner changelog describes fast 10/20/30-second preview and A/B hotkeys. Treat these as UX requirements and remeasure latency in Genre_test.

- [ ] common Web Audio transport;
- [ ] source/candidate asset loading;
- [ ] one playhead and scrubber;
- [ ] 10/20/30 s loop shortcuts plus arbitrary loop;
- [ ] keyboard A/B switching;
- [ ] sample/time alignment metadata;
- [ ] optional loudness matching;
- [ ] waveform;
- [ ] spectrum;
- [ ] spectrogram;
- [ ] stereo/vector visualization;
- [ ] timestamp markers;
- [ ] Delta/null audition;
- [ ] notes and reviewer ratings;
- [ ] blind mode;
- [ ] persist selected winner;
- [ ] converge implementation with #54.

## P4 — resource HUD

P4 expands the minimal P1 adapter into the complete runtime/resource surface.

- [ ] GPU model;
- [ ] VRAM used/total;
- [ ] GPU utilization where supported;
- [ ] temperature/power only when measured;
- [ ] CPU aggregate and optional per-core view;
- [ ] RAM used/total;
- [ ] active backend/model/job;
- [ ] explicit N/A for unsupported telemetry;
- [ ] integrate future #55 residency/unload/fallback events;
- [ ] reject donor duplicate polling backend.

## P5 — Repair UI (#50)

P5 depends on P3 common transport.

### Candidate workflow

- [ ] Original/BYPASS always present;
- [ ] Safe / Probe / Refine candidates;
- [ ] strength/parameters from backend schema, not hardcoded UI assumptions;
- [ ] defect-region loop shortcuts through P3;
- [ ] candidate technical snapshot;
- [ ] Delta audition through P3;
- [ ] loudness-matched comparison through P3;
- [ ] damage warnings;
- [ ] select winner or `FULL_MIX_WINS / REGENERATE_SOURCE / INCONCLUSIVE`.

### Shimmer DSP ideas to benchmark

These are hypotheses, regardless of whether an implementation exists in donor code or only in the changelog:

- [ ] cleanup-before-mastering;
- [ ] high-band-only processing;
- [ ] protected Mid / stronger Side experiment;
- [ ] transient safety gate;
- [ ] fizz/hash detector candidate;
- [ ] cymbal sheen/chatter candidate;
- [ ] ringing/whistle candidate;
- [ ] vocal glaze/sibilance instability candidate;
- [ ] harshness/fatigue candidate;
- [ ] muddy/boxy rescue candidate;
- [ ] spectral Delta by band;
- [ ] clean-control over-processing gate.

No Shimmer constant is promoted without Genre_test fixtures and review.

## P6 — Stems / Vocal (#51 / #52)

P6 depends on P3 common transport. The owner changelog describes Demucs/Blackwell and four-stem monitoring requirements; changelog-only implementation is not direct donor code until pinned.

- [ ] evaluate a reproducible separation backend on pinned Windows runtime;
- [ ] if donor stem code is used, pin exact source/model/checkpoint identity first;
- [ ] verify CUDA path on target Blackwell runtime when relevant;
- [ ] structured CPU fallback;
- [ ] integrate with future `ModelRuntimeManager` rather than private cache;
- [ ] vocals/drums/bass/other cards;
- [ ] per-stem source/processed A/B through P3;
- [ ] stem solo/mute;
- [ ] hand vocals to #51;
- [ ] per-stem TechnicalProfile;
- [ ] latency/phase alignment check;
- [ ] recombination integrity;
- [ ] full-mix Delta;
- [ ] source stems remain immutable.

## P7 — Mastering workstation (#v0.7)

P7 depends on P3 common transport. Do not port Shimmer mastering truth as a competing implementation.

- [ ] mastering backend selector;
- [ ] source preflight;
- [ ] delivery target selector;
- [ ] Safe / Probe / Refine candidate table;
- [ ] Ozone12 optional backend health;
- [ ] REAPER render-host status;
- [ ] XML/preset build guard state;
- [ ] stage progress/heartbeat/cancel;
- [ ] drum-attack retention;
- [ ] mono-loss;
- [ ] decoded codec peaks;
- [ ] LUFS / True Peak / crest / stereo summary;
- [ ] codec-preview candidate;
- [ ] final winner through P3/common Compare surface;
- [ ] preserve `BYPASS IS A VALID WINNER`.

## P8 — Project / Vault / Delivery

- [ ] source + derived asset tree;
- [ ] hash identity;
- [ ] parent/derived graph;
- [ ] processing manifest viewer;
- [ ] analysis/retrieval/model provenance;
- [ ] selected comparison winner;
- [ ] storage footprint;
- [ ] recovery/quarantine operations where applicable;
- [ ] metadata/tag audit;
- [ ] final delivery target where applicable;
- [ ] checksum manifest;
- [ ] JSON/CSV/HTML/PDF reports as appropriate.

## Explicitly rejected donor scope

The owner changelog includes an Anti-AI/Stealth line whose success metric is detector-risk reduction/bypass. That is not a Genre_test product goal.

- [x] reject detector-score minimization;
- [x] reject detector-targeted optimization loops;
- [x] reject watermark/provenance stripping;
- [x] reject origin concealment;
- [x] reject “0% AI risk” as an audio-quality target;
- [x] reject detector-specific presets from the production repair UI.

Generic audio primitives from that line can only re-enter as separately specified audible-repair experiments with BYPASS, clean controls and musical-damage gates.

## Test matrix for migrated UI

- [ ] unit tests for API/domain adapters;
- [ ] web UI smoke with no optional ML backends installed;
- [ ] RU/EN UI smoke;
- [ ] long-job progress/cancel test;
- [ ] restart/resume project state test;
- [ ] source immutability test;
- [ ] derived-output path collision test;
- [ ] desktop GUI regression test;
- [ ] CLI regression test;
- [ ] retrieval unavailable/degraded behavior;
- [ ] mastering backend unavailable behavior;
- [ ] real Windows browser smoke;
- [ ] target-GPU telemetry/runtime smoke when relevant;
- [ ] Audio Science review for any PR changing audio/DSP/listening semantics.

## Graduation principle

The donor migration is complete only when Shimmer is no longer needed as a parallel app to finish a Genre_test project. Useful behavior must be assimilated behind Genre_test contracts, while unavailable changelog-only implementations are reimplemented or later source-pinned, and rejected/duplicate behavior stays out of production.