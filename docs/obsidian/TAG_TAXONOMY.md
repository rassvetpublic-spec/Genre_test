# Taxonomy тегов — Phase 0

Статус: **pre-migration / P0**
Issue: **#169**
Baseline: **Research Radar v2 #142 / PR #167 merged**

## Цель

Задать небольшой контролируемый слой тегов для Obsidian, будущего `KNOWLEDGE_INDEX`, облака тегов и навигации, не создавая конкурирующий Research Radar state.

## Главный принцип

> Tags классифицируют документы. Terms сохраняют точную терминологию. Keywords помогают поиску. Research Radar topic state принадлежит canonical JSON.

Эти слои не смешиваются.

## Ownership boundary

Для research-доменов #169 не создаёт второй independently maintained keyword registry.

Канонические Research Radar topics/keywords принадлежат:

```text
docs/research/data/RADAR_TOPICS.json
```

Generated compatibility:

```text
docs/development/research_radar/KEYWORD_MAP.md
```

является только view этих данных.

Будущий общепроектный keyword layer допустим только в одном из режимов:

1. **generated research view** — выводится из canonical Radar JSON и не редактируется независимо;
2. **non-research index** — содержит только семантику, которой Research Radar не владеет.

> Для одной research-семантики не существует двух независимо редактируемых `KEYWORD_MAP`.

## Структура tags

P0 использует nested tags с русским названием измерения и стабильным техническим slug после `/`.

### Область

```text
область/project
область/retrieval
область/audio-analysis
область/mastering
область/repair
область/runtime
область/research
область/agents
область/delivery
```

### Тип документа

```text
тип/architecture
тип/protocol
тип/reference
тип/research
тип/decision
тип/runbook
тип/status
тип/index
тип/guide
тип/machine-prompt
```

### Статус документа

```text
статус/canonical
статус/active
статус/proposal
статус/reference
статус/archived
статус/generated
```

## Нормализация

- один смысл — один tag;
- spelling variants не создаются;
- technical leaf slugs — lowercase;
- пробелы в tag не использовать; при необходимости использовать `-`;
- nested path — taxonomy, а не имитация файловой структуры;
- human-maintained документ обычно получает 2–5 tags;
- generated subsystem projection может иметь свою domain metadata и не обязана копировать global tags.

## Что не является taxonomy tag автоматически

Не превращать автоматически в tags:

- `CLaMP 3`;
- `MERT`;
- `XLM-R`;
- `Ozone 12`;
- `REAPER`;
- `embedding`;
- `LUFS`;
- `True Peak`;
- `Transient`;
- `Sustain`.

Это предметные `terms`.

Также не создавать tags из малоинформативных высокочастотных слов вроде `system`, `model`, `result`, `test`, `file`, если они не входят в утверждённую taxonomy.

## Terms

`terms` сохраняет точные названия и технический словарь:

```yaml
terms:
  - CLaMP 3
  - MERT
  - XLM-R
  - embedding
  - cosine similarity
```

Будущий `TERM_REGISTRY` может быть canonical **только как словарь терминов в собственной предметной области**: canonical term, русское объяснение, aliases/synonyms, related terms и research-query aliases.

`TERM_REGISTRY` не хранит Research Radar run state, topic status или source status и не переопределяет `RADAR_TOPICS.json`/`SOURCE_REGISTRY.json`.

## Document-local keywords

Пример:

```yaml
keywords_ru:
  - семантический поиск музыки
  - поиск похожих треков
  - аудио-текстовый поиск
keywords_en:
  - music retrieval
  - audio-text retrieval
  - cross-modal music embedding
```

Это hints конкретного документа, а не второй Research Radar registry.

Если смысл принадлежит Research Radar topic, project-wide research indexing получает его из `RADAR_TOPICS.json`, а не из вручную синхронизируемой копии.

## `KNOWLEDGE_INDEX`

Будущий `KNOWLEDGE_INDEX` имеет роль `derived_index`.

Он может агрегировать:

- repository paths;
- document metadata;
- tags;
- terms;
- links/relations;
- pointers на canonical JSON owners;
- generated projection identity.

Он должен быть полностью пересоздаваемым. При расхождении с canonical owner индекс считается stale/invalid.

## Облака и visualizations

- taxonomy cloud строится из утверждённых `tags`;
- term cloud — из `terms` и будущего TERM_REGISTRY;
- Research Radar keyword visualization — из `RADAR_TOPICS.json` либо его deterministic projection.

Visualization никогда не становится state owner.

## Изменение taxonomy

Добавление нового root/canonical tag — schema change.

Mass rename/merge tags проходит отдельный Git branch -> diff -> validation -> PR. UI plugin не является authority.

## Phase 0 boundary

P0 не:

- переписывает существующие tags;
- добавляет frontmatter в живые документы;
- создаёт `TERM_REGISTRY`;
- создаёт `KNOWLEDGE_INDEX`;
- создаёт второй research `KEYWORD_MAP`;
- генерирует облако тегов;
- меняет `docs/research/**` или `docs/development/research_radar/**`;
- выполняет массовую migration.

Detached pilots подтверждают taxonomy concept, но production adoption относится к следующей фазе.