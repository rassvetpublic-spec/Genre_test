---
title: "Genre_test Active Current"
doc_type: status
area: project
status: active
summary: "Текущий engineering snapshot Genre_test на pre-refactor boundary перед SUPERCOMBINE P1."
tags:
  - область/project
  - тип/status
  - статус/active
---

# Genre_test Active Current

Published stable version: **none**

Active development version: **0.5.0.dev0**

Active milestone: **v0.5 CLaMP 3 semantic retrieval**

Milestone epic: **#26**

Long-term product epic: **#49 SUPERCOMBINE**

`Genre_test/main` + live GitHub Issues/PR state — engineering source of truth. Этот файл фиксирует current snapshot, но не заменяет live task state.

## Current boundary state

**PRE-REFACTOR FREEZE.**

```text
mature core / retrieval / QC / legacy Tk presentation
        |
        v
#184 README + Obsidian/Markdown authoring freeze
        |
        v
#171 durable exact-head QA verdict bridge
        |
================ REFACTOR BOUNDARY ================
        |
        v
#164 SUPERCOMBINE P1 workstation
```

P0 workstation architecture #160 / PR #161 уже merged и канонична в `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`.

После boundary:

- старый Tk GUI и CLI остаются compatibility surfaces;
- **новые product features не расширяют Tk presentation architecture**;
- новые UI/service функции реализуются через workstation/application-service architecture;
- Workstation API является adapter над existing Genre_test services, а не вторым backend/source of truth.

## Immediate execution train

1. **#184** — pre-refactor docs/knowledge freeze;
2. **#171** — постоянное решение exact-head QA verdict contract;
3. **#164** — Workstation P1: shell, RU/EN, local service/API/job facade, runtime HUD adapter;
4. **#94** — fail-closed explicit history correctness gate должен быть закрыт до Catalog/Search Workstation P2 acceptance;
5. **#34** — Catalog/Search functional integration в Workstation P2.

`#155 ReviewEvidencePackV1` архитектурно разблокирован после Option C, но на boundary имеет состояние `PARKED_READY`, чтобы не смешивать большой QA-infrastructure track с P1 refactor train.

## Protected ordinary-analysis baseline

```text
Audio
  -> MAEST Discogs519
  -> AudioSet AST
  -> BPM / key / native source metadata
  -> deterministic profile fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor views
  -> history / Validation / build comparison
```

Retrieval, workstation, repair и mastering не меняют эти semantics без отдельной reviewed/versioned migration.

Runtime baseline:

- Python `3.13` primary;
- Python `3.12` fallback;
- Python `3.11` unsupported;
- PyTorch `2.12.1`;
- CUDA `13.0` / cu130;
- RTX 5070 Ti / `sm_120` verified;
- CPU-only supported;
- FFmpeg required for extended decode fallback;
- **#27 runtime compatibility/isolation** — completed; selected runtime is the isolated persistent Python 3.12 CLaMP 3 sidecar.

Supported user entry point: `Genre_test_START.cmd`.

## v0.5 retrieval state

Selected production/reference family:

```text
Audio -> MERT -> CLaMP 3 SAAS
Text  -> XLM-R -> CLaMP 3 SAAS
```

Runtime: optional isolated persistent Python 3.12 sidecar.

Foundation already in `main`:

- versioned retrieval contracts/schema;
- persistent track/text/segment embeddings;
- exact cosine index and deterministic ranking;
- audio similarity search;
- RU multilingual text search;
- representative/custom segment search;
- CLI/export/query history;
- benchmark/catalog acceptance tooling;
- model-free `mfcc-acoustic78` benchmark baseline.

Remaining v0.5 work is predominantly real-catalog/relevance acceptance, selected product descriptions, release policy/packaging and Workstation integration. Exact checklist: `docs/CLAMP3_TODO.md`.

MERT licensing/provenance release gate remains #41. It does **not** block Workstation P1 shell refactoring.

## Catalog/Search presentation ownership

Historical v0.5 UI wording `Анализ | Каталог | Поиск | Validation | Проверка` is no longer a command to add new feature tabs to Tk.

Issue #34 now owns the **functional** Catalog/Search requirements for Workstation P2:

```text
Project | Analyze | Catalog | Search | Repair | Stems | Master | Compare | Delivery | Settings
```

Existing Tk functionality remains operational during migration; presentation replacement is incremental.

## Resource/runtime ownership

Resource Monitor collector was implemented under #48 and remains canonical telemetry truth.

Workstation HUD must consume/adapt that runtime data. It must not create a second Shimmer/HTTP polling truth. #55 full ModelRuntimeManager stays deferred; #164 may define only minimal DTO seams such as `RuntimeSnapshot`, `BackendCapability` and `JobStatus`.

## Comparison transport ownership

Full #54 A/B/X Comparison Lab remains a later studio-finish feature, but the shared transport kernel is required earlier by Workstation P3 before Repair/Stems/Master surfaces depend on it.

No private repair-only or mastering-only transport should be created.

## MCP state

Option C is selected and merged:

- **Track Q** — bounded read-only engineering/QA evidence consumption, transport-independent and cross-cutting;
- **Track P** — Product MCP façade remains v0.9 after stable local service/API boundaries exist.

Old #146 A/B decision is completed/closed. Product MCP runtime is not current scope.

## Obsidian / repository knowledge

Repository root is one Obsidian Vault. Authority model:

> ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS

Current knowledge layer:

- `docs/obsidian/KNOWLEDGE_REGISTRY.json` — navigation metadata only;
- `docs/obsidian/KNOWLEDGE_INDEX.md` — generated projection;
- `docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md` — post-boundary authoring contract;
- `docs/obsidian/MARKDOWN_LEGACY_BASELINE.json` — grandfathered Markdown blob identities.

New or changed human-maintained Markdown must follow the authoring passport. Unchanged historical docs are not mass-rewritten.

## Ozone 12 mastering consolidation

`Genre_test` is the only active engineering destination for AUDIO_MASTERING.

Canonical boundary:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

Standalone `OZONE12_MASTERING_LAB` and `legacy/OZONE12_MASTERING_LAB/` are frozen provenance/migration evidence. No new writes go to the standalone repository.

Ozone 12 Advanced is optional; REAPER is the Ozone render host. Backend-neutral QC belongs in shared technical layers.

## Governance

`AGENTS.md` remains authoritative.

Normal flow:

```text
Issue -> branch -> PR -> exact-head CI/QA
      -> READY-MTD -> squash merge -> post-merge verify -> cleanup
```

The standing automatic MTD authorization applies only to already-approved scope after required exact-head evidence is complete. Temporary #171 review-format exceptions used for previous cleanup trains do not automatically extend to #164.

## Cold-start rule

A fresh agent must start with `docs/REPOSITORY_COLD_START.md`, then inspect live GitHub state before claiming work. Chat history is never durable authority.
