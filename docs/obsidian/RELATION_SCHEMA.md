# Typed relation schema — Phase 0

Статус: **pre-migration / P0**
Issue: **#169**
Baseline: **Research Radar v2 #142 / PR #167 merged**

## Цель

Определить небольшой набор типизированных связей между human-maintained документами и derived indexes без создания второго источника отношений или состояния поверх subsystem-owned JSON.

## Главный принцип

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Связь записывается у canonical owner соответствующего факта. Generated projection, Graph, Breadcrumbs, Bases и будущий `KNOWLEDGE_INDEX` могут показывать или вычислять эту связь, но не становятся новым владельцем только потому, что отображают её.

## Research Radar boundary

P0 не назначает YAML relations владельцем Research Radar topic/source relationships.

Если отношение уже принадлежит:

```text
docs/research/data/*.json
```

то generated `docs/research/obsidian/**` может сериализовать его через frontmatter/`[[wikilinks]]`, но не должна независимо редактировать ту же связь.

Направление:

```text
canonical Radar JSON -> generated Markdown links/frontmatter -> Graph/Bases
```

Недопустимо:

```text
Radar JSON <-> manually maintained Markdown relation
```

## P0 relation set для human-maintained docs

### `parent`

Документ является логической частью более общего документа/узла.

### `depends_on`

Контракт или процедура требует другого контракта/понятия для корректного применения. Это не просто тематическая близость.

### `implementation_of`

Документ описывает реализацию или конкретизацию более общего архитектурного контракта.

### `supersedes`

Текущий документ явно заменяет более старый документ или решение.

### `superseded_by`

Обратная сторона `supersedes`, обычно применимая к старому/архивному документу.

### `evidence_for`

Документ предоставляет evidence для утверждения, решения, протокола или acceptance gate.

### `research_for`

Human-maintained research document обслуживает конкретную область/решение/эксперимент. Это поле не заменяет canonical Research Radar topic/source mapping.

### `related`

Нейтральная связь, когда более точный тип не подходит. Не использовать как универсальную корзину.

## Пустые relations не добавляются

```yaml
# ПЛОХО
parent: []
depends_on: []
related: []
```

Если связи нет, property отсутствует.

## Направление и обратные edges

Relations направленные, кроме нейтрального `related`.

```text
A implementation_of B
```

не означает автоматически:

```text
B implementation_of A
```

Будущий `KNOWLEDGE_INDEX` может вычислять reverse edges как derived data. Их не нужно вручную дублировать в исходных документах.

## Представление значения

Для human-maintained detached pilots P0 **не фиксирует Wikilink как canonical формат frontmatter**.

Пилоты используют repository-relative path без `.md`:

```yaml
depends_on:
  - docs/CLAMP3_RUNTIME
  - docs/THIRD_PARTY_MODELS
```

Generated subsystem projection может использовать generator-owned UI syntax, включая `[[wikilinks]]`.

Разделение:

```text
canonical human relation contract -> repository-relative target
subsystem generated projection     -> generator-owned UI serialization
```

## Integrity rules будущего validator

Перед production adoption должны проверяться:

- target существует;
- self-reference запрещён без специального случая;
- `supersedes`/`superseded_by` не создают противоречивый цикл;
- relation key входит в утверждённый vocabulary;
- archived/reference документ не становится current authority только из-за relation;
- generated projection не становится source of truth из-за backlinks;
- relation из derived index не переопределяет canonical owner;
- Research Radar relation, принадлежащая JSON, не получает вторую independently maintained YAML-копию.

## Manual notes в generated projections

Manual notes между защищёнными markers могут содержать ссылки и наблюдения, но остаются annotation, а не canonical relation store.

Если annotation должна стать Research Radar fact/state, изменение проходит через соответствующий canonical JSON owner.

## Breadcrumbs / Graph / Bases

- Breadcrumbs — optional UI для typed relationships;
- Graph/Backlinks — визуализация ссылок;
- Bases — derived/tabular view.

Ни один из этих интерфейсов не владеет relation schema или subsystem state.

Если Obsidian и plugins удалены:

- canonical relations остаются в Git-native owners;
- generated projections пересоздаются;
- repository tooling может построить derived graph;
- Researcher не теряет canonical state.

## Pilot result

Три detached pilot показали:

1. relation set достаточен для retrieval architecture;
2. mastering protocol не требует отдельной ontology;
3. `ACTIVE_CURRENT` не требует искусственных relations;
4. пустые arrays не нужны;
5. global schema может сосуществовать с Research Radar generated relations без дублирования owners.

## Phase 0 boundary

Новый relation key после P0 считается schema change.

Массовое добавление/переписывание relations требует отдельного migration scope с Git diff и validation. P0 не изменяет `docs/research/**`, `docs/development/research_radar/**` или живые project documents.