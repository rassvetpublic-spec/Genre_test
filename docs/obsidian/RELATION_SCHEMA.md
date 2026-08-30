# Typed relation schema — Phase 0

Статус: **pre-migration / P0**  
Issue: **#169**  
Зависимость: **#142 / PR #167 Research Radar v2**

## Цель

Определить небольшой набор типизированных связей между human-maintained документами и derived indexes, не создавая второй источник отношений или состояния поверх subsystem-owned JSON.

## Главный принцип

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Связь записывается только у того canonical owner, которому принадлежит соответствующий факт. Generated projection, Graph, Breadcrumbs, Bases и будущий `KNOWLEDGE_INDEX` могут показывать или вычислять эту связь, но не становятся новым владельцем только потому, что содержат её копию.

## Research Radar boundary

P0 не назначает YAML relations владельцем Research Radar topic/source relationships.

Если связь `topic -> source` или иное Research Radar состояние уже канонически хранится в:

```text
docs/research/data/*.json
```

то generated `docs/research/obsidian/**` может визуализировать её через frontmatter/`[[wikilinks]]`, но не должна независимо редактировать ту же связь.

Направление:

```text
canonical Radar JSON -> generated Markdown links/frontmatter -> Graph/Bases
```

а не:

```text
Radar JSON <-> manually maintained Markdown relation
```

## P0 relation set для human-maintained docs

### `parent`

Документ является логической частью более общего документа/узла.

### `depends_on`

Документированный контракт или процедура требует другого контракта/понятия для корректного применения. Это не просто тематическая близость.

### `implementation_of`

Документ описывает реализацию или конкретизацию более общего архитектурного контракта.

### `supersedes`

Текущий документ явно заменяет более старый документ или решение. Использовать только при подтверждённой замене.

### `superseded_by`

Обратная сторона `supersedes`. Обычно нужна в архивном/старом документе после контролируемой миграции.

### `evidence_for`

Документ предоставляет evidence для утверждения, решения, протокола или acceptance gate.

### `research_for`

Human-maintained исследовательский документ обслуживает конкретную область/решение/эксперимент. Это поле не заменяет canonical Research Radar topic/source mapping.

### `related`

Нейтральная связь, когда более точный тип не подходит. Не использовать как универсальную корзину.

## Отсутствие пустых relations

Пустые массивы запрещены:

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

Будущий `KNOWLEDGE_INDEX` может вычислять обратные edges как derived data. Такие вычисленные edges не нужно вручную дублировать в каждом source document.

## Представление значения в P0

Для human-maintained detached pilots P0 **не фиксирует Obsidian Wikilink как канонический формат frontmatter**.

Пилоты используют repository-relative path без `.md`:

```yaml
depends_on:
  - docs/CLAMP3_RUNTIME
  - docs/THIRD_PARTY_MODELS
```

Это правило относится к будущей global human-maintained schema и **не требует переписывать** уже принятый generated Research Radar projection, где generator может использовать `[[wikilinks]]` как UI serialization.

Разделение:

```text
canonical human relation contract -> repository-relative target
subsystem generated projection     -> generator-owned UI syntax allowed
```

## Integrity rules

Перед production adoption relations должны проверяться валидатором:

- target существует;
- target не указывает на сам документ без специально разрешённого случая;
- `supersedes`/`superseded_by` не создают противоречивый цикл;
- relation key входит в утверждённый словарь;
- archived/reference документ не становится current authority через relation;
- generated projection не становится source of truth из-за backlinks;
- relation из derived index не может переопределить canonical owner;
- Research Radar relation, принадлежащая JSON, не должна иметь вторую independently maintained YAML-копию.

## Manual notes в generated projections

Manual notes, сохранённые generator-ом между защищёнными markers, могут содержать обычные ссылки/наблюдения.

Они являются annotation, а не canonical relation store. Если annotation должна стать фактом Research Radar state, изменение должно пройти через соответствующий canonical JSON owner.

## Breadcrumbs / Graph / Bases

Breadcrumbs — UI для typed relationships. Graph/Backlinks — визуализация ссылок. Bases — derived/tabular view.

Ни один из них не владеет relation schema или subsystem state.

Если Obsidian и все plugins удалены:

- canonical relations остаются в Git-native owners;
- generated projection может быть пересоздана;
- Python tooling может построить тот же derived graph;
- Researcher не теряет canonical state.

## P0 pilot questions

Три detached pilot-файла должны ответить:

1. хватает ли relation set для retrieval architecture;
2. нужны ли mastering protocol специальные связи;
3. нужны ли relations вообще для `ACTIVE_CURRENT`;
4. какие relations искусственны;
5. может ли global schema сосуществовать с Research Radar v2 generated relations без дублирования owners.

## Изменение relation schema

Новый relation key после P0 считается schema change.

Массовое добавление/переписывание relations проводится только отдельным migration scope с Git diff и validation. P0 не изменяет `docs/research/**` или `docs/development/research_radar/**`.