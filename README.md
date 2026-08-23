# Genre_test

**Current version: 0.3.0**

Локальный анализатор музыкального жанра для Windows/Linux с MAEST Discogs 519, адаптивным Auto-анализом и системой Validation Lab для проверки сходимости и регрессий между версиями.

## Основной анализ

Genre_test:

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC;
- запускает MTG **MAEST Discogs 519** через Hugging Face Transformers;
- автоматически выбирает репрезентативные 30-секундные окна;
- поддерживает `Auto / Fast / Accurate / Expert`;
- агрегирует детальные Discogs styles и broad families;
- рассчитывает `resolved_genre`, hybrid/primary и evidence-aware confidence;
- оценивает BPM, key/mode, RMS и базовые spectral features;
- сохраняет raw MAEST probabilities для повторной калибровки.

> Жанровая классификация вероятностная. Validation измеряет устойчивость результатов, но не заменяет ручной ground truth.

## Windows GUI

Запуск:

```powershell
.\scripts\gui.ps1
```

или двойным кликом:

```text
scripts\Genre_test_GUI.cmd
```

В v0.3 GUI имеет две вкладки:

```text
Анализ
Validation / Перепроверка
```

### Вкладка «Анализ»

Обычный интерфейс показывает:

- входной файл/папку;
- папку результатов;
- `Device`: `auto / cuda / cpu`;
- `Режим анализа`: `Авто / Быстрый / Точный / Экспертный`.

`Окон` и `Top-K` показываются только в `Экспертный`.

### Режимы

| Режим | Поведение |
|---|---|
| Auto | стартует с минимально достаточного набора и расширяется при неоднозначности |
| Fast | максимум 3 окна |
| Accurate | полный duration-based target |
| Expert | ручные окна и Top-K |

Duration target:

| Длительность | Максимум окон |
|---:|---:|
| < 60 с | 1 |
| 60–120 с | 3 |
| 120–210 с | 5 |
| 210–300 с | 7 |
| 300–420 с | 9 |
| > 420 с | 11 |

Для длинного трека Auto сначала анализирует 5 распределённых окон. Если получен стабильный `primary + high confidence`, он останавливается. Иначе анализ расширяется до полного target.

## Validation Lab v0.3

Validation Lab нужен для систематической отладки анализатора.

Он отвечает на три вопроса:

1. сходятся ли Fast / Auto / Accurate на одном треке;
2. изменился ли результат после обновления Genre_test;
3. какие треки требуют ручной проверки.

### Track ID

Каждый трек получает content-based identity:

```text
track_id = sha256:<hash>
```

Поэтому один и тот же файл после переноса/переименования остаётся тем же треком. Идентичные копии в разных каталогах дедуплицируются.

### Центральная история

По умолчанию на Windows:

```text
%LOCALAPPDATA%\Genre_test\history.sqlite3
```

SQLite хранит:

- logical tracks;
- известные пути файлов;
- все analysis runs;
- raw detailed style scores;
- broad-family scores;
- validation sessions;
- pairwise comparisons.

История локальная и не попадает в Git.

### Версионирование каждого запуска

Новый JSON содержит:

- `schema_version`
- `analyzer_version`
- `run_id`
- `analyzed_at`
- `track_id`
- `analysis_mode`
- `windows_analyzed`
- `window_seconds`
- `internal_top_k`
- `report_top_k`
- `model_id`
- `model_revision`
- `device`
- `git_commit` если Git доступен

JSON snapshots больше не перезаписывают друг друга. Имя содержит версию, режим и prefix run-id, например:

```text
track.genre.0.3.0.auto.a1b2c3d4.json
```

## Fast / Auto / Accurate convergence

Validation-режим `Fast + Auto + Accurate` декодирует трек один раз и использует общий prediction cache. Поэтому одинаковые окна не прогоняются через MAEST повторно для каждого режима.

Сравниваются:

- Fast vs Auto
- Fast vs Accurate
- Auto vs Accurate

Convergence:

```text
HIGH
MEDIUM
LOW
FAIL
```

## Автоматический анализ расхождений

Comparator учитывает:

- broad family;
- resolved fine style;
- primary/hybrid;
- Jensen-Shannon divergence broad probabilities;
- cosine similarity broad probabilities;
- weighted Top-N overlap detailed styles;
- BPM;
- key/mode.

BPM `x`, `x/2` и `x*2` считаются эквивалентными трактовками темпа. Например, `81.5` и `163` отмечаются как `half-double`, а не как критическое расхождение.

Severity:

```text
STABLE
MINOR
SIGNIFICANT
CRITICAL
```

## Перепроверка треков из разных каталогов

Во вкладку Validation можно одновременно добавить, например:

```text
D:\Документы\! SUNO
E:\Music Archive
F:\Old Releases
D:\single_track.mp3
```

Доступны фильтры:

- `Все треки`
- `Только результаты старых версий`
- `Только нестабильные`

И режимы:

- Auto
- Fast
- Accurate
- Fast + Auto + Accurate

## Сравнение версий анализатора

Validation Lab умеет сравнить две сохранённые версии, например:

```text
0.2.1 -> 0.3.0
```

Отчёт показывает:

- число common tracks;
- STABLE / MINOR / SIGNIFICANT / CRITICAL;
- resolved genre match %;
- broad family match %;
- tempo equivalent %;
- key/mode match %;
- per-track причины и drift metrics.

## Legacy JSON import

Старые `*.genre*.json` можно загрузить в SQLite history через GUI или CLI.

Если старый JSON не содержит `track_id`, исходный audio path из поля `path` должен ещё существовать: тогда Genre_test вычислит SHA-256 и сопоставит старый результат с текущим треком.

Старые JSON без metadata получают `analyzer_version = legacy-unknown`.

## CLI — основной анализ

Auto:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --out ".\results"
```

Accurate:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --mode accurate
```

Expert:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --mode expert --windows 9 --top-k 20
```

Batch:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music\Album" --out ".\results"
```

## CLI — Validation

Несколько каталогов с полной проверкой сходимости:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" "E:\Archive" --compare-modes
```

Только старые версии:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter old_versions
```

Только нестабильные:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter unstable
```

Импорт истории JSON:

```powershell
.\.venv\Scripts\genre-test.exe history-import ".\results" "D:\OldResults"
```

Сравнение версий:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.2.1 0.3.0 --mode any
```

Auto-to-Auto:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.3.0 0.3.1 --mode auto
```

## Установка / обновление

Первичная установка:

```powershell
cd C:\GIT\Genre_test
.\scripts\setup.ps1
```

Обновление существующей `.venv` после `git pull`:

```powershell
.\scripts\upgrade.ps1
```

Проверка:

```powershell
.\.venv\Scripts\genre-test.exe doctor
```

## Модель

По умолчанию:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
```

Для строгой воспроизводимости поддерживается `--revision <commit>`. Pin default revision остаётся отдельным P1 gate.

## Репозиторий / безопасность

Не хранятся в Git:

- model weights;
- WAV/FLAC/MP3/M4A/AAC/OGG;
- MP4/MOV/WEBM;
- `results/`;
- SQLite DB и WAL/SHM;
- локальная Validation history.

Код проекта — MIT. Лицензия ML-модели определяется авторами модели отдельно.

## Документация

- `docs/ACTIVE_CURRENT.md`
- `docs/ARCHITECTURE.md`
- `docs/VALIDATION_LAB.md`
- `docs/VALIDATION_BASELINE.md`
- `docs/ROADMAP.md`

## Python

Поддерживается Python **3.11 / 3.12 x64**. На Windows рекомендуется Python 3.12.
