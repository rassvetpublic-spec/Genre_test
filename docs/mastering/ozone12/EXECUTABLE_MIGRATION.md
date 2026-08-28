# Ozone 12 executable migration map

Issue: #101  
Parent consolidation: #100

Source snapshot:

```text
rassvetpublic-spec/OZONE12_MASTERING_LAB
a231b1af2cdb597578d4ea3f2d8cb6df964b1619
```

Universal Core v1.4.1 source package SHA-256:

```text
9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7
```

## Ownership after consolidation

| Legacy responsibility | Genre_test owner | Migration decision |
|---|---|---|
| ElementChain decode/encode | `genre_test.mastering.ozone12.xml` | promoted and made strict |
| Param-map patching | `genre_test.mastering.ozone12.xml` / `genre-test-ozone-xml` | promoted; existing Param nodes only |
| Stereo Imager T/S patching | `genre-test-ozone-xml patch-imager-ts` | promoted with build + active-chain guard |
| Maximizer patching | `genre-test-ozone-xml patch-maximizer` | promoted; Maximizer must be final |
| XML chain/Param audit | `genre-test-ozone-xml audit` | promoted; Markdown + CSV |
| Stage folder/run commands | `genre-test-ozone-xml stage-pack` | promoted and rewired to shared QC |
| `oz12_mastering_meter.py` | `genre_test.technical.mastering_metrics` | retired as active duplicate |
| `oz12_analyze_stage.py` audio deltas | shared technical/QC | not copied as a second analyzer |
| audio helpers in `oz12_common.py` | shared technical/QC | not copied as backend-specific analysis |
| REAPER/Ozone rendering | future mastering backend bridge | intentionally deferred |

## Safety changes made during migration

The migration is not a blind file copy. Legacy scripts contained behavior that no longer matches the confirmed schema or current architecture. The consolidated toolkit therefore:

1. requires `PresetVer=6`, `PluginVer=120002`, `PluginBuild=1331` before mutation;
2. treats decoded `ElementChain` as the source of truth for active modules and order;
3. refuses to patch modules absent from the active chain;
4. refuses to invent missing Param nodes;
5. requires Maximizer to be final for Maximizer mutations;
6. does not implicitly toggle Stereoizer while applying Imager T/S settings;
7. does not carry forward legacy Maximizer Param names that conflict with the confirmed schema;
8. leaves ElementChain rewriting explicit rather than silently changing module order;
9. routes render comparison to `genre-test-mastering-qc` instead of preserving duplicate audio meters.

## Remaining boundary

This migration does not automate REAPER or instantiate Ozone. The later render bridge must consume the same pinned XML identity and module-order semantics, render from immutable source audio, then pass the result through backend-neutral technical/QC gates.
