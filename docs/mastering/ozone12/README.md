# Ozone 12 mastering subsystem

This directory is the canonical Ozone 12 knowledge boundary inside **Genre_test**.

`Genre_test` is the product/orchestrator. **iZotope Ozone 12 Advanced** is an optional mastering backend. The standalone `rassvetpublic-spec/OZONE12_MASTERING_LAB` repository is a migration source and is no longer the destination for new mastering architecture or feature work after #100 lands.

## Runtime target

```text
source audio
  -> Genre_test technical preflight
  -> mastering request / candidate orchestration
  -> REAPER render host
  -> Ozone 12 Advanced
  -> derived WAV 24-bit / 48 kHz
  -> Genre_test technical QC / A-B-X / delivery
```

Current confirmed Ozone XML identity:

```text
PresetVer=6
PluginVer=120002
PluginBuild=1331
```

## Ownership boundary

### Genre_test common technical layer

Backend-neutral measurements belong to Genre_test common QC/TechnicalProfile and must eventually have one implementation shared by repair, mastering and A/B/X:

- transient/drum-attack retention;
- mono retention/loss;
- correlation and Side/Mid diagnostics;
- decoded codec peaks;
- loudness/True Peak and before/after guards;
- derived-asset lineage and processing manifests.

Executable promotion is tracked by #101.

### Ozone-specific layer

Keep here:

- XML schema and ParamID mapping;
- `ElementChain` encode/decode and exact module order;
- preset construction/patching;
- Ozone-version/build guards;
- REAPER + Ozone render integration;
- Ozone-specific module policies.

## Chain policy

Module order is part of the mastering decision. The 16-slot template is a **topology/order map, not a default active chain**. Every module must earn activation; `BYPASS` is a valid winner.

Safe causal direction:

```text
preparation / balance
 -> tonal correction
 -> dynamics / transient shaping
 -> harshness / stabilization
 -> stereo processing
 -> final Dynamic EQ / de-essing
 -> Maximizer / True Peak limiting
```

For drum-forward AI hybrid material, first test the directional hypothesis `focused transient / wider sustain`, then require loudness-matched transient, mono, Side/Mid and codec guards.

## Source policy

Prefer the native/lossless source. If only MP3/AAC survives, keep the lossy file immutable, decode once to float PCM, keep all intermediate processing lossless, preserve `LOSSY_SOURCE` provenance, and audit re-encoding only after the final candidate.

## Imported material

- `core/` — active v1.4.1 process/schema knowledge selected for the integrated subsystem;
- `skills/` — reusable XML/T-S workflow;
- `checklists/` and `templates/` — review artifacts;
- `../../../config/mastering/ozone12/` — profiles and schema tables;
- `../../../tools/mastering/ozone12/` — initial Ozone-specific validators/patchers.

See [`MIGRATION_FROM_OZONE12_MASTERING_LAB.md`](MIGRATION_FROM_OZONE12_MASTERING_LAB.md) for source hashes, omissions and follow-up work.
