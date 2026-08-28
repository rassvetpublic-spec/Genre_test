# Ozone 12 runtime namespace

Optional Ozone 12 Advanced mastering-backend boundary.

Issue #100 established the repository and knowledge/config boundary. Issue #101 separates executable ownership so Ozone-specific XML semantics live here while backend-neutral audio QC lives under `genre_test.technical`.

Current runtime-light modules:

```text
__init__.py   pinned preset/plugin/build identity
xml.py        ElementChain + strict Param mutation primitives
xml_cli.py    executable XML inspect/audit/patch/stage-pack workflow
```

The XML layer requires no Ozone or REAPER installation to import or test. It manipulates preset XML only and rejects unconfirmed build identities for mutations.

Critical invariant: active module order comes from decoded `ElementChain`. `Enabled=1` alone is not evidence that a module is active. Patch operations preserve chain order and never synthesize missing Param nodes.

Ordinary v0.4/v0.5 analysis and retrieval must continue to work when Ozone and REAPER are absent. Full REAPER/Ozone render orchestration remains deferred to the later mastering backend bridge.
