---
title: "Genre_test Repository Cold Start"
doc_type: runbook
area: agents
status: canonical
summary: "Канонический порядок восстановления project state из main и live GitHub без зависимости от истории чатов."
tags:
  - область/agents
  - тип/runbook
  - статус/canonical
---

# Repository cold-start recovery contract

## Purpose

Fresh agent должен восстановить текущее состояние Genre_test только из repository + live GitHub, не полагаясь на предыдущий чат как на durable source of truth.

Минимальный результат cold start:

```text
PRODUCT
CURRENT VERSION
CURRENT MILESTONE
CURRENT ARCHITECTURE
REFACTOR BOUNDARY STATE
PROTECTED BASELINES
COMPLETED / ACTIVE / BLOCKED WORK
GOVERNANCE
ASSIGNED ISSUE / TASK CONTRACT
NEXT ALLOWED ACTION
```

## Authority order

При конфликте источников применяй следующий приоритет:

1. `AGENTS.md` для governance/role authority;
2. live GitHub repository/Issue/PR/check state;
3. `docs/ACTIVE_CURRENT.md` для current snapshot;
4. canonical subsystem architecture/contracts;
5. `ROADMAP.md` и TODO для sequence/planning;
6. external references/research;
7. chat memory.

Chat history никогда не отменяет newer `main` или live GitHub state.

## Required recovery order

Этот список семантически зеркалит `AGENTS.md -> Repository-native context`; изменение порядка требует согласованного governance change.

1. `AGENTS.md` — governance, authority and repository workflow.
2. `docs/ACTIVE_CURRENT.md` — current engineering snapshot and protected baseline.
3. `ROADMAP.md` — phase context and long-term dependencies.
4. Assigned/open GitHub Issue plus current PR/branch state — exact task contract, acceptance criteria, allowed/forbidden paths, collision/claim status and exact-head evidence.
5. Architecture/contracts relevant to affected paths, including `docs/ARCHITECTURE.md` and subsystem owners.
6. Nearby implementation/tests that constrain the change.
7. Required review/evidence rules, including QA and Audio Science triggers.
8. The single next permitted workflow transition, cross-checked with `docs/AGENT_WORKFLOW.md` where applicable.

Для repository entry/navigation также прочитать `README.md`. Для любой изменяемой human-maintained Markdown-документации применить `docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md`.

Если работа касается workstation, дополнительно обязательно прочитать:

- `docs/SUPERCOMBINE_UI_ARCHITECTURE.md`;
- `docs/SUPERCOMBINE_SHIMMER_DONOR_TODO.md`;
- #164 и его текущие dependencies.

Если работа касается retrieval:

- `docs/CLAMP3_ARCHITECTURE.md`;
- `docs/CLAMP3_TODO.md`;
- relevant live Issue.

Если работа касается Ozone/mastering:

- `docs/mastering/ozone12/README.md`;
- relevant Ozone core contract;
- standalone `OZONE12_MASTERING_LAB` не использовать как write destination.

## Live-state rule

Repository documents describe canonical ownership and durable state, while live GitHub provides current Issue/PR/check/branch execution state. Before claiming or merging work, re-read the exact current PR head and live checks. A stale document snapshot never overrides a newer merged `main` or live task state.

## Conflict policy

Если durable documents, live GitHub, Issue contract или current `main` расходятся, не выбирать удобную версию молча. Зафиксировать конфликт, предпочесть newer `Genre_test/main`/live GitHub over historical or chat state, и выполнить bounded reconciliation before product implementation. New/material architecture still requires the authority defined in `AGENTS.md`.

## Current refactor boundary

После merge #184 repository переходит через pre-refactor knowledge freeze к первому production workstation refactor slice. Durable exact-head QA bridge уже завершён через #171 / merged PR #188 и не является оставшейся зависимостью #164.

```text
pre-refactor sanitation / knowledge freeze
        |
        +-- #171 / PR #188 durable QA bridge: COMPLETE
        +-- #184 Obsidian/Markdown boundary: CURRENT GATE
        |
================ REFACTOR BOUNDARY ================
        |
        v
#164 SUPERCOMBINE P1
```

Ключевое правило admission:

> После boundary новые product features не должны добавляться в старую Tk presentation architecture, если только отдельный Issue явно не определяет compatibility fix.

Существующий Tk GUI и CLI не удаляются и должны оставаться рабочими во время strangler migration.

## Task admission

Нельзя выбирать работу только потому, что Issue `open`.

Перед claim:

1. прочитать body и последние comments;
2. проверить, не merged/superseded ли задача фактически;
3. проверить parent/dependency Issues;
4. проверить open PRs и branches на collision;
5. сверить `main` с task assumptions;
6. убедиться, что scope разрешён и не требует нового architecture decision;
7. зафиксировать exact base SHA и branch в Issue.

Если Issue body противоречит newer merged canonical state, сначала выполнить state reconciliation, а не реализовывать устаревшее требование.

## Current presentation ownership

Historical Tk UI — compatibility surface.

Primary future navigation:

```text
Project | Analyze | Catalog | Search | Repair | Stems | Master | Compare | Delivery | Settings
```

- #164 P1 создаёт shell/i18n/local service/API/runtime-HUD adapter;
- #34 functional Catalog/Search requirements реализуются в Workstation P2;
- P3 common #54-compatible A/B/X/Delta transport создаёт общий transport kernel до Repair/Stems/Master presentation;
- P5 Repair UI использует только общий P3 transport и не создаёт частный player/transport owner;
- P7 Mastering UI использует тот же общий P3 transport и Genre_test mastering backend, не создавая отдельный mastering-only player;
- #48 Resource Monitor collector уже canonical; не создавать второй polling backend;
- #54 full Comparison Lab остаётся более поздним feature surface;
- #55 full runtime scheduler остаётся deferred.

## Error semantics before Workstation P2

#94 — hard correctness gate. Explicit missing/invalid retrieval history must fail closed.

Web/API adapter не имеет права преобразовывать infrastructure/source failure в valid-looking empty result.

## Obsidian / Markdown admission

Knowledge principle:

> ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS

Перед изменением human-maintained `.md` проверить `docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md`.

После boundary:

- unchanged grandfathered Markdown может сохранять исторический формат;
- новый `.md` требует approved passport;
- изменяемый grandfathered `.md` требует passport в том же PR;
- generated Research Radar/Obsidian projections имеют отдельный owner/schema;
- `CHECK_OBSIDIAN.cmd` проверяет registry/index и Markdown authoring contract;
- repository CI выполняет stdlib authoring checker даже для docs-only PR, поэтому локальная команда не является единственным enforcement surface.

## GitHub workflow

Normal path:

```text
REQUEST
 -> SCOPED
 -> CLAIMED
 -> IMPLEMENTING
 -> REVIEW
 -> QA / AUDIO_SCIENCE when triggered
 -> READY-MTD
 -> squash merge
 -> post-merge verification
 -> branch cleanup
```

Standing automatic MTD не отменяет exact-head evidence gates и не разрешает scope expansion.

## QA boundary

Issue #171 завершён через merged PR #188. Канонический `qa-verdict-bridge` нормализует только допустимый independent exact-head Codex clean-review signal в commit status `qa-verdict-bridge`; он не выдаёт `READY-MTD`, не заменяет Audio Science и не переживает смену head SHA.

RELEASE_MANAGER агрегирует exact-head evidence; он не превращает свободный prose review в `QA_APPROVED` ad hoc.

## Runtime and repository facts

Current baseline:

- development version `0.5.0.dev0`;
- no packaged stable release;
- Python `3.13` primary / `3.12` fallback;
- PyTorch `2.12.1`;
- CUDA `13.0` / cu130;
- RTX 5070 Ti / `sm_120` verified;
- canonical user launcher `Genre_test_START.cmd`;
- active retrieval epic #26;
- long-term SUPERCOMBINE epic #49.

Always re-check `docs/ACTIVE_CURRENT.md` and live GitHub before treating this snapshot as current.

## Cold-start acceptance test

Cold start is complete only when agent can state:

- exact current `main` SHA;
- active version/milestone;
- whether repository is before/inside/after refactor boundary;
- exact assigned Issue and dependencies;
- whether another branch/PR collides;
- authoritative subsystem contracts;
- protected semantics that cannot change;
- required QA/Audio Science gates;
- next allowed action.

If any of these is unknown, do not invent implementation work from memory.
