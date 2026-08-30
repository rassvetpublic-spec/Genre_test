# Obsidian Knowledge Phase 1 — implementation

Статус: **Phase 1 / repository-native navigation layer**
Issue: **#176**

## Цель

Phase 1 превращает принятый Phase 0 control plane в работающий repository-native слой навигации, не начиная массовую миграцию Markdown.

Главный инвариант остаётся неизменным:

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Phase 1 добавляет два новых слоя:

```text
canonical project documents/state
        +
docs/obsidian/KNOWLEDGE_REGISTRY.json
        |
        v
tools/obsidian_knowledge_sync.py
        |
        v
docs/obsidian/KNOWLEDGE_INDEX.md
        |
        v
Obsidian / Graph / search / future Bases
```

## Authority

`KNOWLEDGE_REGISTRY.json` имеет узкую authority:

```text
knowledge_navigation_metadata_only
```

Он может хранить:

- repository path;
- понятное title/summary;
- approved `doc_type` / `area` / `status`;
- controlled taxonomy tags;
- terms и document-local keywords;
- navigation relations между repository files.

Он **не становится владельцем** технических, governance, research, runtime или mastering facts, уже принадлежащих исходным документам/JSON/subsystem contracts.

`KNOWLEDGE_INDEX.md` полностью generated/rebuildable и не редактируется как отдельная база знаний.

## Research Radar boundary

Research Radar v2 не меняется.

Канонические process contracts:

```text
docs/research/RESEARCH_OPERATING_RULES.md
docs/research/RESEARCH_RADAR.md
```

Канонический mutable Radar state:

```text
docs/research/data/*.json
```

Generated Radar views:

```text
docs/research/obsidian/**
docs/development/research_radar/**
```

Global `KNOWLEDGE_REGISTRY.json` может ссылаться на canonical Radar process documents, но валидатор запрещает регистрировать:

```text
docs/research/data/**
docs/research/obsidian/**
docs/development/research_radar/**
```

Это не позволяет global navigation registry случайно стать второй копией Radar mutable/generated state.

## Совместимость с Rules Hub

Phase 1 сверяется с текущим `rassvetpublic-spec/rassvet-rules-hub`, где параллельно развивается совместимый Obsidian knowledge layer.

Cross-project contract общий:

- `ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS`;
- registry authority ограничена navigation metadata;
- JSON -> generated Markdown only;
- общий `doc_type` vocabulary;
- общий `status` vocabulary;
- общий typed relation vocabulary;
- project-local `area` leaves;
- нет обязательного global `doc_id`;
- нет обязательного `language`;
- нет пустых relation arrays;
- stdlib-only validation/generation;
- Obsidian/plugins/CLI не требуются для integrity/CI.

Rules Hub rules не копируются внутрь Genre_test и не становятся Genre_test project state. Перед финальным merge этой Phase 1 необходимо перечитать свежие Rules Hub `main`, `RULES_INDEX.md`, `core/**`, `github/GITHUB_WORKFLOW.md` и состояние его параллельного Obsidian P1.

## Initial coverage

Phase 1 намеренно регистрирует только principal documents, нужные для project navigation/cold-start:

- project entry/current state;
- agent governance/cold-start;
- CLaMP 3 retrieval architecture;
- Research Radar process contracts;
- Ozone 12 subsystem entry;
- Obsidian Phase 0 control-plane contracts.

Это **не полный inventory репозитория**.

Отсутствие файла в registry не означает, что файл неактуален, вторичен или неканоничен.

Full-repository accounting, frontmatter migration, tag/term analytics, global HOME/Bases и обязательный registration gate относятся к последующим фазам.

## Validator / generator

`tools/obsidian_knowledge_sync.py` использует только Python stdlib.

Проверки включают:

- schema/version/authority/generation-direction;
- approved root/entry fields;
- repository-relative normalized paths;
- запрет absolute/path traversal;
- existence каждого registered source и relation target;
- duplicate paths;
- approved `doc_type`, `area`, `status`;
- exact controlled taxonomy tags;
- non-empty unique optional lists/relations;
- `source_of_truth: true` только при `status: canonical`;
- self-relation rejection;
- Research Radar ownership boundary;
- generated-index drift.

Команды:

```text
python tools/obsidian_knowledge_sync.py --check
python tools/obsidian_knowledge_sync.py --write
```

Без флага `--write` canonical source documents не изменяются.

`--write` изменяет только generated:

```text
docs/obsidian/KNOWLEDGE_INDEX.md
```

## Windows entry point

Для локальной проверки предусмотрен:

```text
CHECK_OBSIDIAN.cmd
```

Он пытается использовать Python 3.13, затем Python 3.12 и затем доступный `python`, после чего выполняет `--check`.

Этот launcher не является user runtime Genre_test и не меняет контракт `Genre_test_START.cmd`.

## Plugin boundary

Phase 1 не требует:

- `.obsidian/`;
- Notebook Navigator;
- Omnisearch;
- Breadcrumbs;
- Dataview;
- Smart Connections;
- Obsidian CLI.

Эти инструменты могут потреблять repository-native metadata/index, но не являются его owner.

## Phase 1 non-goals

Не выполняются:

- mass frontmatter insertion;
- массовая русификация Markdown;
- rename/move/link rewrite;
- `TERM_REGISTRY`;
- global tag/term cloud;
- полный repository inventory;
- `.base`/Canvas deployment;
- plugin installation;
- `.obsidian/` commit;
- изменение Research Radar state;
- изменение audio/runtime/product behavior.

## Следующая фаза

После подтверждения reproducibility Phase 1 отдельный scoped Phase 2 может расширить `KNOWLEDGE_REGISTRY`/derived inventory на весь repository и подготовить:

- global Obsidian HOME;
- native Bases;
- deterministic tag/term/keyword analytics;
- controlled metadata migration;
- repository-wide registration/drift CI gate.

Любое изменение authority, обязательного metadata schema или массовая миграция требуют отдельного Issue/PR и повторной сверки с актуальным Rules Hub.
