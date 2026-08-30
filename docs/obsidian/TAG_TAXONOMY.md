# Taxonomy тегов — Phase 0

Статус: **pre-migration / P0**  
Issue: **#169**  
Зависимость: **#142 / PR #167 Research Radar v2**

## Цель

Задать небольшой контролируемый слой тегов для Obsidian, будущего `KNOWLEDGE_INDEX`, облака тегов и навигации, не создавая конкурирующий Research Radar state.

## Главный принцип

> Tags классифицируют документы. Terms сохраняют точную терминологию. Keywords помогают поиску. Research Radar topic state принадлежит своему canonical JSON.

Эти слои не смешиваются.

## Ownership boundary

Для research-доменов #169 не создаёт второй independently maintained keyword registry.

Канонические Research Radar topics/keywords принадлежат:

```text
docs/research/data/RADAR_TOPICS.json
```

Generated compatibility `docs/development/research_radar/KEYWORD_MAP.md` после #142 является только projection/view этих данных.

Будущий глобальный `KEYWORD_MAP` допустим только в одном из двух режимов:

1. **generated research view** — детерминированно выводится из canonical Research Radar JSON и не редактируется независимо;
2. **non-research index** — содержит только области, которыми Research Radar не владеет, и явно не дублирует research topic semantics.

Правило:

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

### Статус

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
- новые spelling variants не создаются;
- технические leaf slugs используются в lowercase;
- пробелы в tag не использовать; при необходимости — `-`;
- nested path используется для taxonomy, а не для имитации файловой структуры;
- один human-maintained документ обычно получает 2–5 tags;
- generated subsystem projection может иметь собственную domain metadata и не обязана искусственно копировать глобальные tags.

## Что не является tag

Не добавлять как taxonomy tag автоматически:

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

## Keywords human-maintained documents

Пример document-local metadata:

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

Это поисковые hints конкретного документа, а не второй Research Radar registry.

Если смысл уже канонически принадлежит Research Radar topic, глобальная индексация должна получать его из `RADAR_TOPICS.json`, а не вручную синхронизировать копию.

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

Он **не становится более высоким authority** и должен быть полностью пересоздаваемым из canonical repository inputs.

Если `KNOWLEDGE_INDEX` расходится с canonical JSON/Markdown owner, индекс считается stale/invalid.

## Облако тегов и терминов

Облако taxonomy строится из утверждённых `tags`.

Отдельное облако терминов может строиться из `terms` и `TERM_REGISTRY`.

Research Radar keyword visualization должна использовать canonical `RADAR_TOPICS.json` либо его deterministic generated projection.

Visualization никогда не становится источником состояния.

## Изменение taxonomy

Добавление нового root/canonical tag — управляемое schema change.

Массовый rename/merge tags проходит Git branch -> diff -> validation -> PR. UI-плагин не является authority.

## P0 ограничения

P0 не:

- переписывает существующие tags;
- добавляет frontmatter в живые документы;
- создаёт `TERM_REGISTRY`;
- создаёт `KNOWLEDGE_INDEX`;
- создаёт второй research `KEYWORD_MAP`;
- меняет `docs/research/**` или `docs/development/research_radar/**`;
- генерирует облако тегов;
- вводит CI gate.

Эти действия рассматриваются только после принятия #142/PR #167 и завершения metadata pilots.