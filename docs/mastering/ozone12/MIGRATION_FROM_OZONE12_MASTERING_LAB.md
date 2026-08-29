# Migration from OZONE12_MASTERING_LAB

Issue: #100  
Completed executable/common-metrics migration: #101
Migration date: 2026-08-28

## Source identity

Standalone source repository:

```text
rassvetpublic-spec/OZONE12_MASTERING_LAB
main commit: a231b1af2cdb597578d4ea3f2d8cb6df964b1619
source tree: 6a82757305ab918bbb64b47442b927ecd745fd1a
```

Universal Core source artifact:

```text
OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1.zip
SHA-256: 9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7
```

The migration uses v1.4.1 as the active knowledge snapshot. Older duplicated/archival `source_consolidated/` material and frozen distribution ZIPs are not imported as active truth.

## Architecture decision

From this migration onward:

```text
AUDIO_MASTERING ChatGPT project
        -> Genre_test GitHub repository = engineering source of truth
        -> mastering/ozone12 = Ozone-specific subsystem
```

The old repository remains available for history until the executable migration and parity checks are finished, then it can be frozen/archived. New issues, architecture decisions and production code belong in Genre_test.

## Imported in #100

The first consolidation PR intentionally imports the compact active knowledge/config boundary rather than copying the old repository wholesale:

- source-of-truth/workflow/XML/T-S/module/Maximizer/codec/mastering-meter/Suno-lossy protocol documents;
- v1.4.1 chain-slot and T/S capability tables;
- safe/profile YAMLs;
- XML/T-S skill, checklists and templates;
- confirmed build-1331 schema;
- initial ElementChain/Stabilizer/schema validator utilities.

## Deliberately not copied as active architecture

- archived `source_consolidated/` duplicates;
- old distribution ZIPs/manifests whose purpose was packaging the standalone lab;
- per-track/session audio or winner XML;
- duplicate repo-level workflows and standalone project governance;
- the full legacy mastering-meter executable as a second permanent implementation.

The executable toolkit was split by ownership in #101: backend-neutral attack/mono/codec metrics moved to common Genre_test TechnicalProfile/QC, while Ozone XML/preset code remains namespaced under mastering/ozone12. REAPER/Ozone rendering remains a later Genre_test-native v0.7 backend.

## Path normalization note

Some imported v1.4.1 documents preserve historical relative references such as `tables/...` because they are evidence-bearing source material. Operational commands must use the canonical integrated locations and active Genre_test CLI:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
genre-test-mastering-qc
```

New code/docs must use these integrated paths. References to the retired
`tools/stage_toolkit/oz12_mastering_meter.py` are provenance only and must not
appear as operational instructions.

## Non-regression boundary

This consolidation must not change the active v0.4 analysis baseline or v0.5 CLaMP retrieval behavior. No Ozone plugin or REAPER runtime is imported into normal analysis startup. Full render orchestration remains a v0.7 feature.

## Completed merge/freeze record

1. #100 established the canonical integrated boundary.
2. #101 completed executable/common-metric ownership migration.
3. Integrated docs/config became canonical for new mastering work.
4. Standalone `OZONE12_MASTERING_LAB` was frozen as history/provenance.
5. Its P0/autocheck runtime was retired rather than copied; future render
   execution is a new Genre_test-native v0.7 backend milestone.
