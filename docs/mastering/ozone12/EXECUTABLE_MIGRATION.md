# Ozone 12 executable migration map

Issue: #101  
Parent consolidation: #100

Status: **COMPLETE for the approved #101 executable-migration scope**.

Source snapshot:

```text
rassvetpublic-spec/OZONE12_MASTERING_LAB
a231b1af2cdb597578d4ea3f2d8cb6df964b1619
```

Universal Core v1.4.1 source package SHA-256:

```text
9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7
```

## Landed work

- #103 promoted backend-neutral mastering/QC metrics into `genre_test.technical` and exposed `genre-test-mastering-qc`.
- #106 consolidated confirmed Ozone XML/ElementChain/Param mutation into `genre_test.mastering.ozone12` and exposed `genre-test-ozone-xml`.
- Ordinary v0.4/v0.5 analysis/retrieval remains independent of Ozone and REAPER.

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
| legacy repository `refresh_manifests.py` | none | old-repository packaging housekeeping; not migrated |
| legacy `validate_process_only_scope.py` | Genre_test repository hygiene rules/tests | old-repository path policy; not copied |
| legacy `oz12_autocheck.py` repository/archive checks | none | not copied; encodes obsolete repo/archive/Python assumptions |
| P0 evidence semantics from legacy autocheck | future mastering-backend validation | retain conceptually: missing evidence is `BLOCKED`, never `PASS` |
| REAPER/Ozone rendering | future mastering backend bridge | intentionally deferred to the planned mastering phase |

## Why the old autocheck is not copied

The standalone checker is useful as historical evidence but is not a compatible Genre_test runtime component. It is coupled to:

- the old `OZONE12_MASTERING_LAB` repository layout;
- the frozen v1.3 distribution archive and its repository-specific SHA;
- Python 3.12-only assumptions while Genre_test supports Python 3.12–3.13 (3.13 primary/default, 3.12 fallback);
- old repository manifest/process-only scripts;
- the retired `oz12_mastering_meter.py` implementation.

Copying it would reintroduce duplicate architecture and stale release assumptions. The later REAPER/Ozone backend harness should instead reuse only its sound evidence principles:

```text
PASS     = required evidence observed and matched
FAIL     = evidence observed and mismatched
BLOCKED  = required prerequisite/evidence is missing
SKIP     = explicitly non-applicable
```

`BLOCKED` must never be promoted to `PASS`. Future render/readback gates should preserve source/target hashes, plugin identity/version/build, active ElementChain, loaded-state identity, readback result, render invocation state, and negative-test evidence without depending on the legacy repository layout.

## Final disposition of the legacy P0 harness

```text
legacy ARCHITECTURE_v1 / P0.1-P0.7 / tools/autocheck
status: RETIRED / NOT MIGRATED
```

This is an intentional architecture decision, not unfinished migration work.
The standalone harness modeled a separate product, repository layout, package
manifest and duplicate meter stack. Importing it would add obsolete code and
compete with Genre_test ownership.

Only transferable evidence principles remain canonical:

- immutable source and target identities;
- pre-render state/readback verification;
- fail-closed handling of missing or mismatched evidence;
- `BLOCKED` is never reported as `PASS`;
- active `ElementChain`, plugin version/build and render identity are recorded;
- negative render-gate tests must prove that a rejected state does not render.

When v0.7 reaches REAPER/Ozone execution, its harness must be designed natively
around the versioned Genre_test `MasteringBackend` request/result contract and
the shared `genre-test-mastering-qc` implementation. It must not revive or
copy the retired standalone P0/autocheck architecture.

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

## Deferred boundary

The current consolidation is complete without automating REAPER or instantiating Ozone. The later render bridge is a separate planned mastering milestone, not unfinished v0.5 migration work. It must consume the same pinned XML identity and module-order semantics, render from immutable source audio, and pass every result through backend-neutral technical/QC gates.
