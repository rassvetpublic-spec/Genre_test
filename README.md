# Genre_test

**Current version: 0.3.4**

Локальный анализатор музыкального жанра для Windows/Linux с **MAEST Discogs 519**, адаптивным Auto-анализом и Validation Lab для проверки сходимости, истории и регрессий между версиями.

## Основной анализ

Genre_test:

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC;
- запускает MTG MAEST Discogs 519 через Hugging Face Transformers;
- автоматически выбирает репрезентативные 30-секундные окна;
- поддерживает `Auto / Fast / Accurate / Expert`;
- на CUDA объединяет несколько MAEST-окон в GPU batch;
- агрегирует detailed Discogs styles и broad families;
- рассчитывает `resolved_genre`, hybrid/primary и evidence-aware confidence;
- оценивает BPM, key/mode, RMS и базовые spectral features;
- сохраняет raw MAEST probabilities и версионную metadata;
- умеет безопасно остановить длительный анализ кнопкой `ОСТАНОВИТЬ`;
- пишет структурированную performance telemetry в repo-local лог.

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

Над вкладками показываются текущая версия Genre_test и полный pinned MAEST revision. Если FFmpeg отсутствует, GUI выводит заметное красное предупреждение о недоступности AAC/M4A/extended decode fallback.

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

## GPU batch inference — v0.3.3

На CUDA несколько независимых 30-секундных окон подаются в MAEST одним batch. Default batch size — до **8 окон** одновременно.

- Fast: выбранные окна идут одним batch;
- Accurate: весь duration target идёт одним batch;
- Auto: первые 5 окон — один batch; если нужна расширенная проверка, вторым batch считаются только недостающие окна;
- `Fast + Auto + Accurate`: Accurate требует полный target, поэтому все уникальные окна вычисляются один раз и затем переиспользуются Fast/Auto через shared cache.

Если CUDA batch не помещается в VRAM и PyTorch сообщает OOM, batch автоматически уменьшается вдвое и повторяется. Safe Stop остаётся cooperative: текущий CUDA batch завершается целиком, затем операция прекращается на безопасной точке.

## Input QC — v0.3.2+

Очень короткий материал не получает обычный high-confidence genre verdict:

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

Result schema: **3**.

## Resolver v0.3.2+

Если broad-family winner и strongest fine-style evidence противоречат друг другу, resolver больше не сохраняет более слабый fine style с отрицательным `style_margin`.

Такой случай:

- помечается как `hybrid`;
- разрешается в strongest fine style из двух ведущих broad families;
- получает `low-medium` confidence;
- competing style сохраняется как `secondary_style`.

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

Переименование или перенос не создаёт новый logical track. Идентичные копии в разных каталогах дедуплицируются.

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

## Performance telemetry — v0.3.3

Обычный repo-local `genre_test.log` содержит UTC timestamp каждой строки и дополнительные machine-readable записи:

```text
PERF {"event":"analyzer_init", ...}
PERF {"event":"maest_batch", ...}
PERF {"event":"track", ...}
PERF {"event":"analysis_item", ...}
PERF {"event":"analysis_session", ...}
PERF {"event":"validation_session", ...}
```

После префикса `PERF ` находится валидный JSON, поэтому журнал можно автоматически разбирать и сравнивать между версиями.

Per-track telemetry содержит:

```text
total_ms
load_ms
features_ms
identity_ms
select_windows_ms
auto_decision_ms
build_result_ms
inference_total_ms
inference_batch_calls
inference_avg_batch_ms
inference_max_batch_ms
inference_avg_window_ms
windows_analyzed
unique_inference_windows
logical_window_uses
cache_reused_window_uses
batched_inference
batch_size_config
auto_expanded
realtime_factor
realtime_speed_x
```

`realtime_factor` — время обработки / длительность аудио; меньше 1 означает быстрее realtime. `realtime_speed_x` — обратная величина: например `20.0` означает обработку примерно в 20 раз быстрее длительности трека.

Для batch дополнительно логируются end-to-end время с JSON/history persistence, среднее `s/track` и `tracks/min`. Для `Fast + Auto + Accurate` видны число уникальных MAEST inference, число logical window uses и экономия shared cache.

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
history_not_comparable
fast_windows
auto_windows
accurate_windows
standalone_auto_saved_windows_pct
```

Summary дополнительно показывает:

- Auto vs Accurate resolved-genre match %;
- Fast vs Accurate resolved-genre match %;
- теоретическую экономию окон одиночного Auto относительно Accurate;
- число Auto early-stop tracks;
- input QC counts;
- число history-пар, которые нельзя корректно сравнивать.

Важно: при triple-mode запуске `Standalone Auto theoretical windows saved` не означает реальную GPU-экономию этой сессии, потому что Accurate всё равно требует полного target. Реальная работа GPU отражается в `unique_inference_windows`, `inference_batch_calls` и session telemetry.

## Version comparison и NOT_COMPARABLE — v0.3.3

Официальное сравнение версий по умолчанию использует **Auto ↔ Auto**. Режим `any` оставлен только для диагностики и может сопоставить разные analysis modes.

Если одна сторона имеет `INSUFFICIENT_AUDIO` или отсутствующий genre verdict, строка получает:

```text
NOT_COMPARABLE
```

а не `CRITICAL`. Такие строки исключаются из denominator для:

- resolved genre match %;
- broad family match %;
- tempo equivalent %;
- STABLE/MINOR/SIGNIFICANT/CRITICAL counts.

Version CSV/JSON дополнительно содержит:

```text
left_mode
right_mode
left_quality
right_quality
comparable
comparison_reason
```

## Drift comparator

Для сопоставимых результатов учитываются:

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

`NOT_COMPARABLE` является отдельным состоянием отчёта, а не уровнем severity.

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

Повторный v0.3.2 validation после scanner/QC hardening:

```text
180 unique tracks
180 analyzed
0 decode errors
175 verdict-bearing tracks
5 INSUFFICIENT_AUDIO

Auto == Accurate: 175 / 175 = 100.0%
Fast == Accurate: 64.57%
Standalone Auto theoretical windows saved: 100 / 1145 = 8.73%
Auto early-stop tracks: 30
```

Поэтому **Auto принят как основной рабочий режим**.

## Модель и воспроизводимость

Default model:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
```

Pinned default revision:

```text
6c35f32a350f74351870937d5ae0bae1d898d1df
```

Полный revision показывается в GUI, CLI result и сохраняется в result metadata.

Для custom model можно передать собственный:

```text
--revision <commit>
```

## Runtime / decoder diagnostics

```powershell
.\.venv\Scripts\genre-test.exe doctor
```

показывает:

- Genre_test/Python/Torch;
- CUDA runtime/GPU;
- SoundFile version;
- FFmpeg path или заметный `MISSING`;
- AAC/extended decode fallback status;
- Hugging Face token status и источник локального token (без вывода самого token);
- default MAEST model;
- pinned model revision;
- default CUDA inference batch;
- History DB path.

HF token status проверяется локально. `token available` означает, что token найден в environment/cache; это не сетевое подтверждение его валидности.

## FFmpeg bootstrap — v0.3.4

На Windows `setup.ps1` и `upgrade.ps1` теперь автоматически обеспечивают наличие FFmpeg.

Порядок:

1. поиск `ffmpeg` в текущем PATH;
2. поиск WinGet Links, Scoop, Chocolatey и стандартного `Program Files\ffmpeg\bin`;
3. если FFmpeg не найден — автоматическая установка `Gyan.FFmpeg` через WinGet;
4. каталог найденного `ffmpeg.exe` сразу добавляется в PATH текущего процесса;
5. `doctor` повторно показывает фактический путь и статус AAC/extended decode fallback.

Отдельный helper:

```powershell
.\scripts\ensure_ffmpeg.ps1
```

Явный отказ от автоматического bootstrap:

```powershell
.\scripts\setup.ps1 -SkipFFmpeg
.\scripts\upgrade.ps1 -SkipFFmpeg
```

Если `ffmpeg.exe` установлен через WinGet/Scoop/Chocolatey, но новая PowerShell-сессия получила устаревший PATH, Genre_test дополнительно обнаруживает известный путь и добавляет его в PATH текущего Python-процесса перед `librosa.load()`.

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

Версия:

```powershell
.\.venv\Scripts\genre-test.exe --version
```

`--version` является лёгкой командой: она не импортирует Torch/Transformers и проверяется отдельным CI smoke на Python 3.11/3.12.

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

Основное сравнение версий:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.3.1 0.3.2 --mode auto
```

Диагностический any-mode:

```powershell
.\.venv\Scripts\genre-test.exe compare-versions 0.3.1 0.3.2 --mode any
```

## Установка / обновление

Первичная установка:

```powershell
cd C:\GIT\Genre_test
.\scripts\setup.ps1
```

На Windows `setup.ps1` автоматически проверяет и при необходимости устанавливает FFmpeg через WinGet.

Обновление после `git pull`:

```powershell
.\scripts\upgrade.ps1
```

`upgrade.ps1` выполняет ту же проверку FFmpeg, поэтому существующая установка Genre_test автоматически дооснащается decoder dependency после обновления.

Проверка:

```powershell
.\.venv\Scripts\genre-test.exe --version
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