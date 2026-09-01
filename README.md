---
title: "Genre_test"
doc_type: guide
area: project
status: active
summary: "Главная точка входа в Genre_test: текущее состояние, pre-refactor boundary, runtime, retrieval, SUPERCOMBINE и канонические документы."
tags:
  - область/project
  - тип/guide
  - статус/active
---

# Genre_test

**Current development version:** `0.5.0.dev0`

**Published stable release:** none

**Current architecture state:** **PRE-REFACTOR FREEZE**

Genre_test — локальный Windows-first проект для анализа, semantic retrieval и последующего studio-finish generative audio. Канонический продукт развивается в одном репозитории; отдельные analyzer, retrieval, repair, mastering и UI реализации не должны становиться параллельными источниками истины.

## Refactor boundary

Репозиторий находится в формально зафиксированной точке перед переходом к SUPERCOMBINE workstation architecture.

```text
mature core / retrieval / QC / legacy Tk presentation
        |
        v
PRE-REFACTOR FREEZE  (#184)
        |
        +-- current truth reconciled
        +-- new Tk feature development stops
        +-- Obsidian/Markdown authoring contract becomes enforceable
        +-- durable exact-head QA contract is resolved (#171)
        |
================ REFACTOR BOUNDARY ================
        |
        v
#164 SUPERCOMBINE P1
        |
        +-- local workstation shell
        +-- RU/EN i18n
        +-- local application-service/API facade
        +-- runtime HUD adapter
        |
        v
P2 Analyze / Catalog / Search
        |
        v
P3 common Compare transport / A-B-X / Delta foundation
```

После этой границы **новые product features не расширяют старую Tk presentation architecture**. Существующий desktop GUI и CLI остаются поддерживаемыми compatibility surfaces до завершения strangler-migration.

Каноническая workstation architecture: [`docs/SUPERCOMBINE_UI_ARCHITECTURE.md`](docs/SUPERCOMBINE_UI_ARCHITECTURE.md).

## Product north star

```text
Generated mix / stems
  -> Analyze
  -> Catalog / Search
  -> Technical QC + markers
  -> Repair
  -> Stems / Vocal
  -> Mix / Master
  -> synchronized Compare
  -> Metadata / Delivery
```

Главные инварианты:

- source audio immutable;
- measured/model evidence отделено от descriptions/recommendations;
- каждый derived asset получает provenance/processing identity;
- optional heavy backends fail independently;
- destructive operations previewable/reversible;
- AI-origin detector evasion, watermark stripping и provenance concealment не являются целями продукта.

Long-term epic: **#49 SUPERCOMBINE**. Текущий retrieval epic: **#26**.

## Current protected analysis baseline

Ordinary Analyze сохраняет существующую модель:

```text
Audio
  -> MAEST Discogs519
  -> AudioSet AST
  -> BPM / key / native source metadata
  -> deterministic fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor views
  -> history / Validation / build comparison
```

Retrieval, Workstation, Repair и Mastering не имеют права молча менять этот baseline без отдельной versioned migration.

Pinned model/runtime details: [`docs/MODELS.md`](docs/MODELS.md), [`docs/ACTIVE_CURRENT.md`](docs/ACTIVE_CURRENT.md).

## Active v0.5 retrieval

Selected backend family: **CLaMP 3 SAAS + MERT + XLM-R** через optional isolated persistent Python 3.12 sidecar.

Уже существуют foundation для:

- persistent track/text/segment embeddings;
- exact cosine catalog index;
- audio-to-audio search;
- Russian multilingual text-to-audio search;
- representative/custom segment search;
- CLI/export/benchmark/catalog-acceptance tooling;
- model-free `mfcc-acoustic78` benchmark baseline.

Оставшиеся задачи v0.5 в основном относятся к real-catalog acceptance, reviewed relevance benchmark, release policy и workstation integration. Live task state всегда определяется GitHub Issues, а не этим README.

Архитектура retrieval: [`docs/CLAMP3_ARCHITECTURE.md`](docs/CLAMP3_ARCHITECTURE.md).

Execution checklist: [`docs/CLAMP3_TODO.md`](docs/CLAMP3_TODO.md).

## Workstation migration rule

Primary new UI surface после boundary:

```text
Project | Analyze | Catalog | Search | Repair | Stems | Master | Compare | Delivery | Settings
```

Правило слоёв:

```text
Workstation Web UI
        |
Local application-service / job API
        |
canonical Genre_test services + backend adapters + shared QC
        |
SQLite / project state / derived-asset manifests
```

Web API — adapter, **не второй backend**.

Issue #34 теперь хранит functional Catalog/Search requirements для Workstation P2. Resource Monitor collector, уже реализованный по #48, остаётся единственной runtime telemetry truth; workstation HUD только адаптирует его представление.

## Ozone 12 mastering boundary

`Genre_test` — единственный активный engineering destination для AUDIO_MASTERING.

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

`OZONE12_MASTERING_LAB` и `legacy/OZONE12_MASTERING_LAB/` — frozen migration/provenance evidence. Новые записи в standalone Ozone repository не выполняются.

Ozone 12 Advanced остаётся optional mastering backend, REAPER — его render host. Ordinary Analyze/Retrieval не должны зависеть от Ozone или REAPER.

Подробнее: [`docs/mastering/ozone12/README.md`](docs/mastering/ozone12/README.md).

## Obsidian knowledge system

Repository root используется как **один Obsidian Vault** без второго mutable knowledge store.

Принцип:

> ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS

Navigation registry: [`docs/obsidian/KNOWLEDGE_REGISTRY.json`](docs/obsidian/KNOWLEDGE_REGISTRY.json)

Generated index: [`docs/obsidian/KNOWLEDGE_INDEX.md`](docs/obsidian/KNOWLEDGE_INDEX.md)

Markdown authoring contract: [`docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md`](docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md)

После pre-refactor freeze:

- historical unchanged Markdown grandfathered по Git blob identity;
- новый human-maintained `.md` обязан иметь approved passport;
- изменяемый historical `.md` мигрирует на passport в том же PR;
- generated Research Radar/Obsidian projections сохраняют собственный owner/schema.

Локальная проверка:

```powershell
.\CHECK_OBSIDIAN.cmd
```

## Runtime and startup

Supported runtime:

- Python `3.13` x64 primary;
- Python `3.12` x64 supported fallback;
- Python `3.11` unsupported;
- PyTorch `2.12.1`;
- CUDA `13.0` / cu130;
- RTX 5070 Ti / `sm_120` proven on target workstation;
- CPU-only mode supported;
- FFmpeg required for extended decode fallback.

Supported user entry point:

```powershell
.\Genre_test_START.cmd
```

Examples:

```powershell
.\Genre_test_START.cmd retrieval-status
.\Genre_test_START.cmd retrieval-setup
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
```

No packaged stable release is currently published.

## Canonical project entry points

Read in this order for current engineering work:

1. [`AGENTS.md`](AGENTS.md) — governance and role authority;
2. [`docs/REPOSITORY_COLD_START.md`](docs/REPOSITORY_COLD_START.md) — recovery procedure;
3. [`docs/ACTIVE_CURRENT.md`](docs/ACTIVE_CURRENT.md) — current snapshot and boundary state;
4. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — protected architecture baseline;
5. [`ROADMAP.md`](ROADMAP.md) — product/release sequence;
6. [`docs/SUPERCOMBINE_UI_ARCHITECTURE.md`](docs/SUPERCOMBINE_UI_ARCHITECTURE.md) — post-boundary workstation architecture;
7. live GitHub Issues/PRs — exact task contract and next allowed action.

If chat history conflicts with `main` + live GitHub state, repository/GitHub wins.

## Governance

`main` is protected. Normal change flow is:

```text
Issue -> scoped branch -> implementation -> PR -> exact-head CI/QA
      -> READY-MTD -> squash merge -> post-merge verify -> branch cleanup
```

Standing automatic MTD applies only to already-approved scope after all exact-head gates are satisfied. It never authorizes missing evidence, architecture expansion or bypassing QA.
