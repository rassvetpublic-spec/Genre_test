# Genre_test

**Current version: 0.3.2**

Локальный анализатор музыкального жанра для Windows/Linux с **MAEST Discogs 519**, адаптивным Auto-анализом и Validation Lab для проверки сходимости, истории и регрессий между версиями.

## Основной анализ

Genre_test:

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC;
- запускает MTG MAEST Discogs 519 через Hugging Face Transformers;
- автоматически выбирает репрезентативные 30-секундные окна;
- поддерживает `Auto / Fast / Accurate / Expert`;
- агрегирует detailed Discogs styles и broad families;
- рассчитывает `resolved_genre`, hybrid/primary и evidence-aware confidence;
- оценивает BPM, key/mode, RMS и базовые spectral features;
- сохраняет raw MAEST probabilities и версионную metadata;
- умеет безопасно остановить длительный анализ кнопкой `ОСТАНОВИТЬ`.

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

GUI имеет две вкладки:

```text
Анализ
Validation / Перепроверка
```

Обе вкладки поддерживают безопасную остановку длительных операций и копирование всего текстового результата в буфер обмена. Постоянный лог можно открыть из интерфейса.

## Режимы анализа

| Режим | Поведение |
|---|---|
| Auto | основной режим; начинает с достаточного минимума и расширяется при неоднозначности |
| Fast | максимум 3 репрезентативных окна |
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

## Input QC — v0.3.2

Очень короткий материал больше не получает обычный high-confidence genre verdict:

```text
< 10 s   -> INSUFFICIENT_AUDIO
            genre verdict не выдаётся

10-30 s  -> SHORT_INPUT
            одно padded MAEST window
            confidence не выше medium

>= 30 s  -> NORMAL
```

В JSON/CSV сохраняются:

```text
input_quality
quality_notes
```

Result schema v0.3.2: **3**.

## Resolver v0.3.2

Если broad-family winner и strongest fine-style evidence противоречат друг другу, resolver больше не сохраняет более слабый fine style с отрицательным `style_margin`.

Теперь такой случай:

- помечается как `hybrid`;
- разрешается в strongest fine style из двух ведущих broad families;
- получает `low-medium` confidence;
- competing style сохраняется как `secondary_style`.

Это отдельно закрывает реальные cross-family случаи, обнаруженные большим v0.3.1 benchmark.

## Validation Lab

Validation Lab отвечает на три вопроса:

1. сходятся ли Fast / Auto / Accurate на одном треке;
2. изменился ли результат после обновления Genre_test;
3. какие треки требуют ручной проверки.

### Track ID

Каждый трек получает content identity:

```text
track_id = sha256:<hash>
```

Переименование или перенос не создают новый logical track. Идентичные копии в разных каталогах дедуплицируются.

### Центральная история

По умолчанию runtime data остаются внутри checkout:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\.genre_test\huggingface\
C:\GIT\Genre_test\results\
```

`.genre_test/` и `results/` gitignored.

SQLite хранит:

- logical tracks;
- известные пути файлов;
- все analysis runs;
- raw detailed style scores;
- broad-family scores;
- validation sessions;
- pairwise comparisons.

## Fast / Auto / Accurate convergence

Режим:

```text
Fast + Auto + Accurate
```

декодирует трек один раз и использует общий prediction cache. Одинаковые окна не прогоняются через MAEST повторно.

Сравниваются:

```text
Fast vs Auto
Fast vs Accurate
Auto vs Accurate
```

Convergence:

```text
HIGH
MEDIUM
LOW
FAIL
```

## Mode convergence и History drift

С v0.3.2 эти две вещи больше не смешиваются в объяснении результата.

**Mode convergence** сравнивает режимы текущего запуска.

**History drift** сравнивает текущие результаты с предыдущими сохранёнными runs/версиями.

Validation JSON/CSV содержит отдельно:

```text
severity
mode_severity
mode_worst_pair
mode_reasons
history_severity
history_reasons
fast_windows
auto_windows
accurate_windows
auto_saved_windows_pct
```

Summary дополнительно показывает:

- Auto vs Accurate resolved-genre match %;
- Fast vs Accurate resolved-genre match %;
- количество и процент окон, сэкономленных Auto;
- число Auto early-stop tracks;
- input QC counts.

## Drift comparator

Учитываются:

- broad family;
- resolved fine style;
- primary/hybrid;
- Jensen-Shannon divergence;
- cosine similarity;
- weighted Top-N overlap;
- BPM;
- key/mode.

BPM `x`, `x/2` и `x*2` считаются эквивалентными трактовками темпа.

Severity:

```text
STABLE
MINOR
SIGNIFICANT
CRITICAL
```

## Recursive scanner hygiene

При выборе каталога по умолчанию игнорируются:

```text
.git
.venv
.genre_test
results
__pycache__
Resources/audioAlg
```

Это не даёт внутренним cache/resource-фрагментам DAW/обработки загрязнять genre benchmark.

Во вкладке Validation включён checkbox:

```text
Игнорировать служебные каталоги
```

CLI override:

```text
--include-service-dirs
```

Если файл выбран явно, он анализируется даже внутри normally ignored directory.

## Реальный validation baseline — 2026-08-23

Полный v0.3.1 Fast + Auto + Accurate catalog run:

```text
291 найденных путей
241 unique SHA-256 tracks
225 analyzed successfully
16 decode errors skipped
50 duplicate paths
0 remaining

STABLE      173
MINOR        25
SIGNIFICANT  27
CRITICAL      0

Auto == Accurate resolved genre: 225 / 225 = 100.0%
Fast == Accurate resolved genre: 181 / 225 = 80.4%
```

Поэтому **Auto принят как основной рабочий режим**. После v0.3.2 рекомендуемый regression run — `Только нестабильные` + `Fast + Auto + Accurate`, а не повторный полный triple-mode каталог.

## Модель и воспроизводимость

Default model:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
```

Default revision pinned в v0.3.2:

```text
6c35f32a350f74351870937d5ae0bae1d898d1df
```

Для default MAEST новые runs больше не должны содержать:

```text
model_revision: null
```

Для custom model можно передать собственный:

```text
--revision <commit>
```

## Decoder diagnostics

```powershell
.\.venv\Scripts\genre-test.exe doctor
```

показывает:

- Genre_test/Python/Torch;
- CUDA runtime/GPU;
- SoundFile version;
- FFmpeg path или `MISSING`;
- AAC/extended decode fallback status;
- default MAEST model;
- pinned model revision;
- History DB path.

## Перепроверка треков из разных каталогов

Validation может одновременно принимать каталоги и отдельные файлы с разных дисков.

Фильтры:

```text
Все треки
Только результаты старых версий
Только нестабильные
```

Режимы:

```text
Auto
Fast
Accurate
Fast + Auto + Accurate
```

## CLI

Обычный Auto:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav"
```

Accurate:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --mode accurate
```

Batch:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music\Album"
```

Validation convergence:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" "E:\Archive" --compare-modes
```

Только нестабильные:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --filter unstable --compare-modes
```

Включая служебные каталоги для специальной диагностики:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --compare-modes --include-service-dirs
```

Импорт history JSON:

```powershell
.\.venv\Scripts\genre-test.exe history-import ".\results" "D:\OldResults"
```

Сравнение версий:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.3.1 0.3.2 --mode auto
```

## Установка / обновление

Первичная установка:

```powershell
cd C:\GIT\Genre_test
.\scripts\setup.ps1
```

Обновление после `git pull`:

```powershell
.\scripts\upgrade.ps1
```

Проверка:

```powershell
.\.venv\Scripts\genre-test.exe doctor
```

## Репозиторий / безопасность

Не хранятся в Git:

- model weights;
- WAV/FLAC/MP3/M4A/AAC/OGG;
- MP4/MOV/WEBM;
- `results/`;
- `.genre_test/`;
- SQLite DB/WAL/SHM;
- локальный runtime log/cache.

Код проекта — MIT. Лицензия ML-модели определяется авторами модели отдельно.

## Документация

- `docs/ACTIVE_CURRENT.md`
- `docs/ARCHITECTURE.md`
- `docs/VALIDATION_LAB.md`
- `docs/VALIDATION_BASELINE.md`
- `docs/RUNTIME_DATA.md`
- `docs/ROADMAP.md`

## Python

Поддерживается Python **3.11 / 3.12 x64**. На Windows рекомендуется Python 3.12.
