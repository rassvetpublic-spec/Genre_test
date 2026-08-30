# Схема Properties для Obsidian — Phase 0

Статус: **pre-migration / P0**  
Issue: **#169**  
Baseline: **Research Radar v2 #142 / PR #167 merged**

## Главный инвариант

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Верхняя граница истины проекта — Git repository. Канонический формат определяется владельцем конкретного знания или состояния, а не Obsidian и не удобством конкретного плагина.

Допустимая модель:

```text
Git repository
  |
  +-- canonical contracts / knowledge: Markdown (+ YAML Properties where adopted)
  +-- canonical structured mutable state: JSON where subsystem contract says so
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

Недопустимая модель:

```text
canonical JSON <-> independently edited Markdown state <-> Obsidian database
```

Удаление Obsidian, community plugins и локальной `.obsidian/` конфигурации не должно приводить к потере проектного знания или состояния.

## Research Radar v2 — уже принятый владелец

P0 не переопределяет архитектуру Research Radar v2.

Канонические process contracts:

```text
docs/research/RESEARCH_OPERATING_RULES.md
docs/research/RESEARCH_RADAR.md
```

Канонический mutable machine state:

```text
docs/research/data/RADAR_TOPICS.json
docs/research/data/SOURCE_REGISTRY.json
docs/research/data/RESEARCH_STATE.json
```

Специализированные registries, например:

```text
docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json
```

сохраняют authority в своих утверждённых предметных областях.

Research Obsidian projection после PR #167:

```text
docs/research/obsidian/
  RESEARCH_HOME.md
  RESEARCH_STATE.md
  TOPICS/topic__<id>.md
  SOURCES/source__<id>.md
```

Это generator-owned projection. Mutable Radar state идёт только в направлении:

```text
canonical JSON -> generated Markdown -> Graph / Bases / CLI / Omnisearch
```

Двусторонняя JSON <-> Markdown синхронизация в P0 запрещена.

Historical compatibility facade:

```text
docs/development/research_radar/**
```

также generated view и не является вторым источником истины.

## Единый Vault и федеративные слои

Vault root = **корень репозитория `Genre_test/`**.

`docs/obsidian/` не является Vault root. Это общепроектный human-maintained control plane для Obsidian/knowledge architecture.

```text
Genre_test/                         <- ONE VAULT
  docs/obsidian/                    <- global control plane
  docs/research/obsidian/           <- generated Research projection
```

Будущий общий Obsidian HOME/dashboard может ссылаться на:

```text
docs/research/obsidian/RESEARCH_HOME.md
```

но не должен копировать mutable Research Radar state в independently maintained Properties.

## Классы repository knowledge

### 1. `canonical_document`

Human/machine-readable Markdown contract или knowledge document, который является владельцем утверждения в своей области.

### 2. `canonical_machine_state`

Структурированное изменяемое состояние, для которого subsystem contract назначил машинный формат владельцем. Research Radar JSON — текущий пример.

Obsidian Properties не копируют такой state как независимый authority.

### 3. `generated_projection`

Производное представление канонических данных для человека, Obsidian или compatibility surface.

Generated frontmatter допустим, но его поля не становятся владельцем исходных фактов.

### 4. `derived_index`

Пересоздаваемый индекс для поиска, навигации или аналитики.

Будущий `KNOWLEDGE_INDEX` относится к этому классу и не может переопределять canonical owners.

### 5. `visualization`

Canvas, Graph, word cloud и другие представления. Canvas-only project facts запрещены.

## Properties для human-maintained документов

P0 предлагает небольшой общий паспорт, но **не применяет его массово**.

Кандидат обязательного минимума после отдельной migration phase:

| Property | Тип | Назначение |
|---|---|---|
| `title` | string | Человекочитаемое русское название |
| `doc_type` | string | Тип документа из контролируемого словаря |
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

## Generated subsystem projections имеют свою schema

Нельзя заставлять generator-owned projection искусственно копировать human-maintained passport.

Research Radar v2 уже использует domain-specific поля класса:

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

1. canonical owner однозначно определён;
2. projection детерминированно генерируется и проверяется;
3. generated metadata не редактируется как второй state;
4. отключение Obsidian не лишает проект исходного состояния.

Global `PROPERTY_SCHEMA` задаёт ownership rules и общий vocabulary, а не единый гигантский YAML для всех subsystem generators.

## Manual notes в generated Research projection

Ручные Obsidian notes допускаются только внутри:

```text
<!-- MANUAL-NOTES-START -->
...
<!-- MANUAL-NOTES-END -->
```

Они являются `annotation_only`, сохраняются generator-ом и не могут переопределить canonical JSON. Например, запись `topic X = PAUSED` в manual notes не меняет Radar state.

> Preserved annotation may enrich a view, but may not override the canonical owner.

## Язык

Для human-facing документации целевой язык объяснения — русский.

Точные технические идентификаторы сохраняются в исходном виде: имена моделей, API, CLI-команды, schema/field names, repository paths, классы, форматы, plugin names и международные research terms.

`language: ru` **не является обязательным полем в P0**. Русский рассматривается как будущий default; исключения могут указывать язык явно, когда это полезно machine tooling.

Generated projections могут сохранять язык своего subsystem generator; массовая русификация Research Radar projection не входит в #169.

## Опциональные свойства human-maintained Markdown

Добавляются только когда несут полезные данные.

| Property | Тип | Когда использовать |
|---|---|---|
| `aliases` | list[string] | Английское название, сокращение, старое название, синоним |
| `terms` | list[string] | Точные технические термины и модели |
| `keywords_ru` | list[string] | Русские document-local поисковые формулировки |
| `keywords_en` | list[string] | Международные document-local поисковые формулировки |
| `reader_level` | enum | `basic`, `intermediate`, `expert`, `machine` |
| `source_of_truth` | bool | Только если документ действительно authority в своей области |
| `language` | string | Когда нужен явный язык |
| typed relations | list[string] | Только реальные связи из `RELATION_SCHEMA.md` |

Не добавлять пустые свойства ради одинаковой формы:

```yaml
# ПЛОХО
aliases: []
terms: []
keywords_ru: []
keywords_en: []
parent: []
depends_on: []
related: []
```

Если свойства нет — оно отсутствует.

## `doc_id`

`doc_id` **не является обязательным в P0**.

Стабильный отдельный identifier вводится только если будущий индексатор/миграция докажет, что repository path недостаточен — например для внешнего foreign key или сохранения identity через rename/move.

Domain entity ID существующего subsystem, например Research Radar `canonical_id`, не считается глобальным `doc_id`.

## `tags` != `terms` != `keywords`

- `tags` — небольшой контролируемый классификатор;
- `terms` — точная предметная терминология;
- `keywords_ru` / `keywords_en` — document-local discovery metadata;
- Research Radar `keywords` в `RADAR_TOPICS.json` — canonical research topic semantics в своей области.

Для одной research-семантики запрещён второй independently maintained `KEYWORD_MAP`.

## P0 candidate vocabularies

Типы документов:

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

Области:

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

Статусы документов:

```text
canonical
active
proposal
reference
archived
generated
```

Расширение этих словарей после P0 считается schema change.

## Detached pilot

До изменения реальных документов schema проверяется на трёх отдельных metadata-файлах:

- retrieval: `docs/CLAMP3_ARCHITECTURE.md`;
- mastering: `docs/mastering/ozone12/core/03_TRANSIENT_SUSTAIN_PROTOCOL.md`;
- current/governance state: `docs/ACTIVE_CURRENT.md`.

Исходные документы в P0 не изменяются.

Research Radar v2 служит отдельным compatibility case для generated projections, но #169 не изменяет Radar-owned paths.

## Результат пилота

P0 зафиксировал:

- обязательный `doc_id` пока не нужен;
- `language: ru` не нужен как обязательное поле;
- пустые relation arrays не нужны;
- retrieval и mastering укладываются в общий relation vocabulary;
- `ACTIVE_CURRENT` не требует искусственных typed relations;
- document-local keywords полезны для discovery, но не становятся Research Radar authority.

## Критерий принятия

Schema пригодна к следующей фазе, если:

1. один факт имеет одного canonical owner;
2. structured Research Radar state остаётся JSON-owned;
3. generated projections нельзя принять за independently editable state;
4. `docs/obsidian/` и `docs/research/obsidian/` имеют разные ownership roles;
5. retrieval/mastering/current описываются без metadata-шумa;
6. точные технические термины не теряются;
7. Properties можно индексировать без community plugin;
8. Obsidian можно удалить без потери knowledge/state;
9. новый Markdown не требует десятков обязательных полей.

## Phase 0 boundary

P0 не разрешает:

- массовую миграцию Markdown;
- mass `property:set`;
- массовый rename/move;
- создание второго Research Radar state/keyword owner;
- внедрение `KNOWLEDGE_INDEX` или `TERM_REGISTRY`;
- обязательную зависимость от Obsidian/plugins/CLI;
- изменение `docs/research/**` или `docs/development/research_radar/**`.

Следующая migration phase должна быть отдельным Issue/PR scope.