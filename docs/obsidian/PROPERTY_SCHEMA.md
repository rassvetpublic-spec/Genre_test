# Схема Properties для Obsidian — Phase 0

Статус: **pre-migration / P0**
Issue: **#169**
Baseline: **Research Radar v2 #142 / PR #167 merged**

## Главный инвариант

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Верхняя граница истины проекта — Git repository. Канонический формат определяется владельцем конкретного знания или состояния, а не Obsidian и не возможностями конкретного plugin.

Допустимо:

```text
Git repository
  +-- canonical contracts / knowledge: Markdown (+ YAML Properties where adopted)
  +-- canonical mutable machine state: JSON where subsystem contract says so
  |
  v
generators / validators
  |
  v
derived Markdown / indexes / projections
  |
  v
Obsidian Graph / Bases / CLI / Omnisearch / Canvas
```

Недопустимо:

```text
canonical JSON <-> independently edited Markdown state <-> Obsidian database
```

Удаление Obsidian и community plugins не должно приводить к потере project knowledge/state.

## Research Radar v2 baseline

P0 не переопределяет Research Radar.

Canonical process contracts:

```text
docs/research/RESEARCH_OPERATING_RULES.md
docs/research/RESEARCH_RADAR.md
```

Canonical mutable machine state:

```text
docs/research/data/RADAR_TOPICS.json
docs/research/data/SOURCE_REGISTRY.json
docs/research/data/RESEARCH_STATE.json
```

Specialized registries, например `docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json`, сохраняют authority в своих областях.

Generated Research Obsidian projection:

```text
docs/research/obsidian/
  RESEARCH_HOME.md
  RESEARCH_STATE.md
  TOPICS/topic__<id>.md
  SOURCES/source__<id>.md
```

Historical compatibility facade:

```text
docs/development/research_radar/**
```

Для mutable Radar state направление только:

```text
canonical JSON -> generated Markdown -> Graph / Bases / CLI / Omnisearch
```

Двусторонняя JSON <-> Markdown sync в P0 запрещена.

## Один Vault, федеративные слои

Vault root = **корень репозитория `Genre_test/`**.

```text
Genre_test/                         <- ONE VAULT
  docs/obsidian/                    <- global human-maintained control plane
  docs/research/obsidian/           <- generated Research Radar projection
```

`docs/obsidian/` не является отдельным vault и не копирует Radar mutable state.

Будущий global HOME может ссылаться на:

```text
docs/research/obsidian/RESEARCH_HOME.md
```

но не должен хранить independently maintained копию Research state.

## Классы repository knowledge

### `canonical_document`

Markdown contract/knowledge document — owner утверждений в своей области.

### `canonical_machine_state`

Структурированное изменяемое состояние, чей subsystem contract назначил machine format canonical owner. Research Radar JSON — текущий пример.

### `generated_projection`

Производное представление canonical data. Generated frontmatter может обслуживать UI/Graph/Bases, но не становится owner исходных facts.

### `derived_index`

Полностью rebuildable индекс поиска/навигации/аналитики. Будущий `KNOWLEDGE_INDEX` относится сюда.

### `visualization`

Canvas, Graph, word cloud и другие views. Canvas-only project facts запрещены.

## Human-maintained Properties

P0 предлагает маленький общий passport, но **не применяет его к живым документам**.

Кандидат будущего обязательного минимума:

| Property | Тип | Назначение |
|---|---|---|
| `title` | string | Человекочитаемое русское название |
| `doc_type` | string | Тип документа |
| `area` | string | Основная область проекта |
| `status` | string | Роль документа |
| `summary` | string | Короткое понятное описание |
| `tags` | list[string] | Малый набор taxonomy tags |

Пример:

```yaml
---
title: "Архитектура семантического поиска CLaMP 3"
doc_type: architecture
area: retrieval
status: canonical
summary: "Как Genre_test строит CLaMP 3 audio/text retrieval и изолирует runtime от Core Analyze."
tags:
  - область/retrieval
  - тип/architecture
  - статус/canonical
---
```

## Generated projections имеют собственную schema

Generator-owned Markdown не обязан искусственно копировать human passport.

Research Radar v2 уже использует поля класса:

```yaml
id:
canonical_id:
type:
generated:
canonical_owner:
generation_direction:
status:
keywords:
exclusions:
topics:
canonical_path:
run_sequence:
```

Это допустимо, если:

1. canonical owner однозначен;
2. projection детерминированно генерируется/проверяется;
3. generated metadata не редактируется как второй state;
4. отключение Obsidian не лишает проект canonical data.

Global `PROPERTY_SCHEMA` задаёт ownership rules и vocabulary, а не один гигантский YAML для всех subsystems.

## Manual notes в generated Research projection

Ручные notes допускаются только внутри:

```text
<!-- MANUAL-NOTES-START -->
...
<!-- MANUAL-NOTES-END -->
```

Они `annotation_only`, сохраняются generator-ом и не могут переопределить canonical JSON.

## Язык

Human-facing explanation целевой — русский.

Точные technical identifiers сохраняются в оригинальном виде: model names, API, CLI commands, field/schema names, repository paths, class names, formats, plugin names и international research terms.

`language: ru` **не является обязательным полем P0**. Русский рассматривается как будущий default, а явный `language` нужен только когда это полезно machine tooling или язык отличается.

Generated subsystem projections могут временно сохранять язык generator-а; массовая русификация Research Radar projection не входит в #169.

## Опциональные Properties

Добавляются только когда несут данные.

| Property | Тип | Когда использовать |
|---|---|---|
| `aliases` | list[string] | English name, сокращение, старое название, синоним |
| `terms` | list[string] | Точные technical terms/models |
| `keywords_ru` | list[string] | Русские document-local search hints |
| `keywords_en` | list[string] | Международные document-local search hints |
| `reader_level` | enum | `basic`, `intermediate`, `expert`, `machine` |
| `source_of_truth` | bool | Только для реального authority |
| `language` | string | Когда язык нужно указать явно |
| typed relations | list[string] | Реальные связи из `RELATION_SCHEMA.md` |

Пустые arrays не добавляются:

```yaml
# ПЛОХО
aliases: []
terms: []
keywords_ru: []
parent: []
depends_on: []
```

Если значения нет — property отсутствует.

## `doc_id`

`doc_id` **не обязателен в P0**.

Отдельный stable ID вводится только если будущий indexer докажет, что repository path недостаточен — например для внешнего foreign key или identity через rename/move.

Domain ID существующего subsystem, например Radar `canonical_id`, не является глобальным `doc_id`.

## `tags` != `terms` != `keywords`

- `tags` — контролируемая навигационная taxonomy;
- `terms` — точная предметная терминология;
- `keywords_ru` / `keywords_en` — document-local discovery hints;
- Research Radar `keywords` в `RADAR_TOPICS.json` — canonical research topic semantics.

Нельзя создавать второй independently maintained research `KEYWORD_MAP`.

## P0 candidate vocabularies

Document types:

```text
architecture
protocol
reference
research
decision
runbook
status
index
guide
machine_prompt
```

Areas:

```text
project
retrieval
audio-analysis
mastering
repair
runtime
research
agents
delivery
```

Document statuses:

```text
canonical
active
proposal
reference
archived
generated
```

Расширение vocabulary после P0 считается schema change.

## Detached pilots

Schema проверяется без изменения исходных документов:

- `docs/CLAMP3_ARCHITECTURE.md`;
- `docs/mastering/ozone12/core/03_TRANSIENT_SUSTAIN_PROTOCOL.md`;
- `docs/ACTIVE_CURRENT.md`.

P0 создаёт только соответствующие `docs/obsidian/pilot/*.metadata.yaml`.

Research Radar v2 используется как generated-projection compatibility case, но #169 не изменяет Radar-owned paths.

## Pilot findings

- обязательный `doc_id` пока не нужен;
- `language: ru` не нужен как mandatory field;
- пустые relation arrays не нужны;
- retrieval/mastering укладываются в общий relation vocabulary;
- `ACTIVE_CURRENT` не требует artificial relations;
- document-local keywords полезны, но не становятся Research Radar authority.

## Phase 0 boundary

P0 не разрешает:

- массовую Markdown migration/translation;
- mass `property:set`;
- mass rename/move/link rewrite;
- второй Research Radar state/keyword owner;
- внедрение `KNOWLEDGE_INDEX` или `TERM_REGISTRY`;
- обязательную зависимость от Obsidian/plugins/CLI;
- изменение `docs/research/**` или `docs/development/research_radar/**`.

Следующая migration phase должна иметь отдельный Issue/PR scope.