# Ozone 12 tools

This directory contains Ozone-specific material migrated from `OZONE12_MASTERING_LAB`.

## Active executable boundary

The supported XML entry point is:

```text
genre-test-ozone-xml
```

It is implemented in `genre_test.mastering.ozone12` and provides:

- preset identity inspection;
- strict ElementChain decode and safe encode;
- XML base/candidate audit with Markdown/CSV reports;
- strict JSON Param-map patching;
- guarded Stereo Imager Transient/Sustain patching;
- guarded Maximizer patching that requires Maximizer to be final;
- repeatable stage-pack generation.

Patch operations are intentionally conservative:

- pinned `PresetVer=6`, `PluginVer=120002`, `PluginBuild=1331` are required;
- the target module must be present in `ElementChain`;
- only Param nodes already present in the source XML are mutated;
- unknown/missing ParamIDs fail instead of being synthesized;
- module order is never inferred from `Enabled=1`;
- the CLI does not silently rewrite ElementChain order.

## Shared metrics are not duplicated here

The old standalone `oz12_mastering_meter.py`, `oz12_analyze_stage.py`, and their shared audio-analysis helpers are **not** active Genre_test architecture. Their backend-neutral responsibilities were promoted to:

```text
genre_test.technical.mastering_metrics
genre-test-mastering-qc
```

That shared layer owns transient retention, mono loss/correlation and decoded-codec peak validation for repair, Ozone, A/B/X and future mastering backends.

## Legacy reference files

`tools/mastering/ozone12/xml_patch/` retains selected source-snapshot validators/examples for provenance and regression reference. New executable XML behavior should use the package CLI/core rather than creating another independent patching framework.

REAPER/Ozone render orchestration remains a later mastering-backend bridge and is not a dependency of normal Genre_test analysis/retrieval startup.
