---
title: "Genre_test Markdown Authoring Standard"
doc_type: protocol
area: project
status: canonical
summary: "Канонический контракт оформления новых и изменяемых human-maintained Markdown-документов после pre-refactor freeze."
tags:
  - область/project
  - тип/protocol
  - статус/canonical
---

# Genre_test Markdown Authoring Standard

## Authority

Этот документ — канонический authoring-контракт для human-maintained Markdown после граничной точки рефакторинга #184.

Главный принцип knowledge layer:

> ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS

Git/repository documents, live GitHub state и subsystem contracts остаются источниками истины. Obsidian, Graph, Bases, search, generated indexes и plugins являются представлениями и не получают отдельную authority.

## Transition rule

Исторические Markdown-файлы не переписываются массово ради frontmatter.

Boundary snapshot хранится в `docs/obsidian/MARKDOWN_LEGACY_BASELINE.json` и фиксирует Git blob identity существующих human-maintained Markdown на commit `107df368fc5fc85f310e84a88a5247e62d1e7c51`.

Правило после boundary:

1. неизменённый grandfathered Markdown может оставаться в старом формате;
2. новый human-maintained `.md` обязан иметь паспорт из этого документа;
3. grandfathered `.md`, содержимое которого изменено после boundary, обязан получить паспорт в том же изменении;
4. generated projections и subsystem-owned generated Markdown используют собственный schema/owner и не мигрируют по этому контракту;
5. замена факта новой копией запрещена — нужно изменить canonical owner или сослаться на него.

## Required passport

Новый или мигрированный human-maintained Markdown начинается с YAML-compatible frontmatter:

```yaml
---
title: "..."
doc_type: architecture|protocol|reference|research|decision|runbook|status|index|guide|machine_prompt
area: project|retrieval|audio-analysis|mastering|repair|runtime|research|agents|delivery
status: canonical|active|proposal|reference|archived|generated
summary: "..."
tags:
  - область/<area>
  - тип/<doc-type>
  - статус/<status>
---
```

`tags` должны точно соответствовать `area`, `doc_type` и `status`. Для `doc_type` с `_` в tag используется `-`.

Validator намеренно поддерживает ограниченный детерминированный YAML-compatible subset без внешнего YAML runtime. Quoted scalar должен начинаться и заканчиваться одной и той же одинарной или двойной кавычкой; незакрытые или несовпадающие кавычки запрещены. Сложные inline YAML structures вместо контролируемого passport subset не используются.

Разрешённые дополнительные properties определяются `docs/obsidian/PROPERTY_SCHEMA.md`, `docs/obsidian/RELATION_SCHEMA.md` и `docs/obsidian/TAG_TAXONOMY.md`. Пустые optional arrays запрещены.

## Document structure

Human-maintained документ после миграции должен:

- иметь ровно один H1 в column-zero ATX форме `# Heading`;
- использовать только column-zero ATX headings (`#` ... `######`); Setext headings и ATX headings с начальным отступом запрещены;
- использовать H2/H3/... и не перескакивать через уровень заголовка;
- держать repository paths, commands, identifiers, schema names, model IDs и exact values в code formatting;
- ссылаться на существующего canonical owner вместо копирования большого блока уже принадлежащих ему фактов;
- явно указывать ограничения и authority для `proposal`, `reference` и `research` материалов;
- использовать repository-relative Markdown links или устойчивые Obsidian wiki-links, когда это действительно улучшает навигацию;
- не делать Canvas, plugin database, local cache или Obsidian GUI единственным местом хранения факта;
- сохранять UTF-8 и LF line endings;
- не содержать secrets, tokens, private credentials или машинно-зависимое локальное состояние как проектную истину.

## Technical language

Русский остаётся предпочтительным языком пользовательской и operating-документации, но технические identifiers не переводятся и не переименовываются ради стилистики.

Примеры того, что должно сохраняться точно:

- `AudioProfile`;
- `TechnicalProfile`;
- `RetrievalBackend`;
- `QA_APPROVED <40-char-sha>`;
- `docs/ACTIVE_CURRENT.md`;
- `CLaMP 3` / `MERT` / `XLM-R`;
- `Ozone 12 Advanced` / `REAPER`.

## Exempt generated/owned paths

Global Markdown authoring checker не применяет human passport к:

- `docs/development/research_radar/**` — отдельный Research Radar process/facade owner;
- `docs/research/obsidian/**` — generated Research Radar projection;
- `docs/obsidian/KNOWLEDGE_INDEX.md` — generated from `KNOWLEDGE_REGISTRY.json`;
- `.github/**`, `src/**`, `tools/**`, `legacy/**`, `releases/**` — вне Phase 2 human-doc scope этого контракта.

Исключение не означает, что путь неважен или неканоничен. Оно означает только, что у него другой format/schema owner.

## Validation

Локальная проверка:

```powershell
.\CHECK_OBSIDIAN.cmd
```

Прямая проверка authoring contract:

```powershell
python tools/check_markdown_authoring.py
```

Проверка fail-closed для:

- нового non-compliant Markdown;
- изменённого grandfathered Markdown без паспорта;
- невалидных `doc_type` / `area` / `status`;
- несовпадающих controlled tags;
- отсутствующего или множественного H1;
- Setext/indented heading syntax;
- пропуска heading level;
- malformed/unbalanced quoted passport scalar;
- CRLF/CR в новом или мигрированном документе.

## Refactor boundary

После merge #184 новые product features не должны расширять старую Tk presentation architecture. Старый desktop GUI остаётся compatibility surface; новые UI/service changes идут через SUPERCOMBINE workstation architecture, начиная с #164.
