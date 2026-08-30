# Obsidian CLI Policy — Phase 0

Статус: **pre-migration / P0**  
Issue: **#169**  
Зависимость: **#142 / PR #167 Research Radar v2**

## Назначение

Официальный Obsidian CLI рассматривается как **optional local interface** к Git-backed vault Genre_test.

Он не является источником истины, не требуется CI, не требуется облачному Researcher и не должен хранить критическое состояние, отсутствующее в Git-файлах.

Главный инвариант:

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Для Research Radar mutable state владельцем остаётся canonical JSON. Если будущий утверждённый workflow использует CLI для записи, он должен изменять соответствующий canonical owner, а не generated Markdown projection.

## Runtime limitation: CLI не headless backend

Obsidian CLI требует работающий desktop Obsidian process. Если приложение не запущено, первая команда может запустить GUI.

Следствия:

- CLI не является backend для GitHub Actions;
- cloud/remote Researcher не может зависеть от наличия CLI;
- CLI предполагается использовать на локальной рабочей машине с доступом к vault;
- все критические validators должны работать напрямую с Markdown/YAML/JSON без Obsidian.

## Уровни доступа

### READ

Операции без изменения canonical files/state.

Примеры классов команд:

```text
read
search
search:context
property:read
backlinks
links
unresolved
orphans
deadends
base:query
```

READ разрешён локальным инструментам, если задача требует чтения vault и команда не вызывает скрытую mutation.

### SAFE_WRITE

Локальные ограниченные изменения заранее известного набора файлов.

Примеры:

```text
create
append
prepend
property:set
property:remove
move
rename
base:create
```

SAFE_WRITE допускается только:

1. в Git working tree;
2. в отдельной branch;
3. с заранее ограниченным scope;
4. с последующим `git diff`;
5. после repository validators;
6. через обычный PR workflow.

Название команды само по себе не определяет риск: массовый `property:set` по сотням файлов считается DANGEROUS.

### DANGEROUS

Операции, способные уничтожить данные, массово переписать vault, выполнить произвольный код или изменить runtime Obsidian.

В этот класс входят:

```text
delete / permanent delete
overwrite
eval
plugin install / uninstall
массовый property:set / property:remove
массовый rename / move
```

`obsidian eval` считается выполнением произвольного JavaScript внутри Obsidian и не является штатным API Genre_test.

DANGEROUS-операция требует отдельного явно ограниченного task scope. P0 такие операции не разрешает.

## Git как транзакционный предохранитель

Для любой WRITE-операции:

```text
git status
-> clean/understood working tree
-> dedicated branch
-> bounded mutation
-> git status
-> git diff
-> validators/tests
-> PR
```

Mass-write нельзя начинать из dirty working tree, если существующие изменения пересекаются с затрагиваемыми файлами.

## Git / live Obsidian race

Obsidian и Git работают с одним деревом файлов. Поэтому массовые операции Git могут пересекаться с открытым/редактируемым buffer в Obsidian.

Особенно рискованны:

```text
git checkout / switch
git pull
git merge
git rebase
git restore
массовый rename / move
```

Перед массовой Git-операцией:

1. завершить редактирование затрагиваемых notes;
2. убедиться, что изменения сохранены на диск;
3. закрыть затрагиваемые tabs/notes либо временно закрыть Obsidian при широком scope;
4. выполнить Git operation;
5. снова проверить vault и `git status`.

`git status clean` не доказывает отсутствие активного редакторского состояния внутри GUI.

## Research Radar v2 boundary

CLI не меняет ownership model #142.

Канонический mutable state:

```text
docs/research/data/RADAR_TOPICS.json
docs/research/data/SOURCE_REGISTRY.json
docs/research/data/RESEARCH_STATE.json
```

Generated projection:

```text
docs/research/obsidian/**
```

Compatibility generated view:

```text
docs/development/research_radar/**
```

Если CLI редактирует generated projection вне защищённых manual-note blocks, такое изменение не является способом изменить Research Radar state и может быть перезаписано generator-ом.

Manual notes между:

```text
<!-- MANUAL-NOTES-START -->
<!-- MANUAL-NOTES-END -->
```

являются annotation-only и не переопределяют canonical JSON.

P0 #169 не выполняет CLI writes в Radar-owned paths.

## CI policy

CI Genre_test не должен требовать:

- установленный Obsidian;
- запущенный GUI;
- Obsidian CLI;
- community plugins;
- plugin cache;
- локальные embeddings/indexes.

CI/validators работают напрямую с Git-native inputs:

```text
Markdown
YAML Properties
JSON
repository links/paths
```

## Bases / Canvas / Graph

CLI-доступ к Bases или другим Obsidian views не делает их каноническими.

- Bases = derived view/query layer;
- Canvas = visualization/navigation layer;
- Graph/Backlinks = derived visualization;
- Omnisearch = derived retrieval surface.

Критический факт должен иметь canonical owner в Git-backed contracts/state до отображения этими интерфейсами.

## `.obsidian/`

`.obsidian/` целиком в Git не добавляется.

Допускается только отдельно утверждённая portable-конфигурация. По умолчанию не коммитятся:

- plugin binaries;
- caches;
- embeddings;
- локальные indexes;
- workspace/session state;
- machine-specific paths;
- credentials/API keys/secrets.

## VaultQuery

Статус P0:

```text
DEFERRED / NOT APPROVED
```

SQL write-layer не требуется, пока задачи закрываются repository tooling, официальным CLI и Bases без дополнительного массового write surface.

## Phase 0 constraints

P0 разрешает проектирование policy, detached metadata pilots и read-only proof-of-concept.

P0 не разрешает:

- массовый `property:set`;
- массовый rename/move;
- `eval` как штатный механизм;
- dependency CI/Researcher от CLI;
- mutation Research Radar projection/state;
- двустороннюю JSON/Markdown sync;
- массовую миграцию документации.

## Итоговое правило

> Obsidian CLI — удобный официальный локальный интерфейс, но не источник истины и не инфраструктурная зависимость.

> Всё критичное должно воспроизводиться напрямую из Git repository без запущенного Obsidian.