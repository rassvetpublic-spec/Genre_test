# Genre_test 0.4.0

Локальный музыкальный анализатор и лаборатория регрессионной проверки для Windows.

**Текущий стабильный релиз: 0.4.0.** В активной ветке проекта поддерживается только актуальная v0.4-линия; portable 0.3.x выведен из эксплуатации.

## Что умеет Genre_test

Один анализ строит `AudioProfile` из нескольких независимых источников:

```text
Audio
  ├─ MAEST Discogs519 ── detailed genre/style + broad-family evidence
  ├─ AudioSet AST ────── semantic evidence: genre / vocal / instruments / mood / production
  └─ DSP/librosa ─────── BPM / key / source audio metadata
             ↓
        Evidence fusion
             ↓
         AudioProfile
      ├─ Обычный
      ├─ SUNO
      └─ Дистрибьютор
```

Основные результаты:

- основной жанр и broad family;
- confidence и secondary influence;
- соседние стили;
- semantic production/vocal/instrument evidence;
- BPM с half / 2⁄3 / double альтернативами;
- key/mode;
- исходные sample rate / bit depth / channels / bitrate;
- SUNO `Style of Music`;
- distributor genre/subgenre;
- JSON, CSV и центральная SQLite history;
- Validation и сравнение сохранённых сборок.

## Быстрый старт — рабочий Git checkout

Рекомендуемый каталог в Windows:

```text
C:\GIT\Genre_test
```

После клонирования или обновления запускайте:

```powershell
cd C:\GIT\Genre_test
.\Genre_test_START.cmd
```

Первый запуск автоматически готовит окружение. Повторные запуски переиспользуют совместимые компоненты.

Launcher проверяет или устанавливает:

- WinGet / App Installer;
- Microsoft Visual C++ 2015–2022 x64 Runtime;
- Python 3.11 / 3.12 / 3.13 x64;
- Python 3.12 x64 как fallback, если совместимого Python нет;
- project-local `.venv`;
- PyTorch 2.12.1;
- NVIDIA: CUDA 13.0 / cu130;
- Blackwell native architecture, включая `sm_120`;
- CPU PyTorch на настоящих CPU-only системах;
- FFmpeg;
- pinned MAEST и AudioSet AST runtime;
- `genre-test doctor`.

На CPU-only машине штатный статус:

```text
CUDA: N/A | GPU: N/A
```

Если NVIDIA физически обнаружена, но PyTorch CUDA/native architecture не работает, это считается ошибкой runtime, а не скрытым CPU fallback.

## Portable release

Готовый пакет находится в двух местах:

1. GitHub Release `v0.4.0`;
2. папка [`releases/`](releases/) в репозитории.

Основной архив:

```text
Genre_test_0.4.0_portable.zip
```

Проверочный файл:

```text
SHA256SUMS.txt
```

Внутри ZIP нет Python, PyTorch и весов моделей. Они подготавливаются при первом запуске. Распакуйте архив в обычный локальный каталог и запустите `Genre_test_START.cmd`.

Подробная portable-инструкция: [`README_RU.txt`](README_RU.txt).

## GUI

По умолчанию используется тёмная тема. Справа сверху доступно живое переключение `Тёмная / Светлая` без перезапуска.

Основные вкладки:

### Анализ

Обычная работа с одним файлом или каталогом.

Доступны:

- Device: `auto / cuda / cpu` в зависимости от Runtime Health;
- режим: `auto / fast / accurate / expert`;
- вывод: `all / normal / suno / distributor`;
- полный путь;
- Expert: число MAEST-окон и Top-K;
- Safe Stop.

На CPU-only компьютере пункт `cuda` не показывается.

### Validation

Повторный анализ и диагностика:

- mode convergence;
- history drift;
- unstable-only / stale-or-missing recheck;
- Fast / Auto / Accurate сравнение;
- Safe Stop;
- отчёты JSON/CSV.

Маркеры вида `[DRIFT: STABLE]` описывают **стабильность относительно history/другого режима**, а не confidence жанрового решения.

### Проверка

Сравнение уже сохранённых build identity без повторного анализа аудио.

Build identity включает:

```text
analyzer version + git commit + schema + model revision
```

Перед сравнением показывается покрытие A/B/common. Если общих результатов нет, программа не выводит бессмысленные `0%` метрики.

## Режимы анализа

| Режим | Назначение |
|---|---|
| `Auto` | основной режим; расширяет число окон только при неоднозначности |
| `Fast` | быстрый диагностический проход, до 3 окон |
| `Accurate` | полный duration-based target |
| `Expert` | ручное число окон и Top-K |

Input QC:

```text
< 10 s   → INSUFFICIENT_AUDIO
10–30 s  → SHORT_INPUT, 1 padded MAEST window, confidence ≤ medium
>= 30 s  → NORMAL
```

## Модели и воспроизводимость

MAEST:

```text
mtg-upf/discogs-maest-30s-pw-129e-519l
revision: 6c35f32a350f74351870937d5ae0bae1d898d1df
```

AudioSet AST:

```text
MIT/ast-finetuned-audioset-10-10-0.4593
revision: f826b80d28226b62986cc218e5cec390b1096902
```

Result schema: **4**.

MAEST остаётся главным detailed-style классификатором. AST даёт независимое semantic/broad-family evidence. Слабый AST-сигнал не получает полный вес только потому, что оказался единственным распознанным semantic genre tag.

Финальные `Genre` и `Family` согласуются: профиль не должен публиковать взаимоисключающие пары вида `Indie Pop / Electronic`.

## Tempo / BPM

Tempo-v2 учитывает типичные неоднозначности:

```text
half
2/3
base
3/2
2x
```

Для коротких и breakcore/half-double материалов сохраняются альтернативные кандидаты. Стабильный повтор одного и того же результата не означает автоматически, что BPM является ground truth — проблемные tempo cases должны иметь независимую ручную разметку.

## History и runtime data

По умолчанию в рабочем checkout:

```text
.genre_test\history.sqlite3
.genre_test\logs\genre_test.log
results\
```

`track_id` строится по SHA-256 содержимого, поэтому переименование или перенос файла не создаёт новый logical track.

History хранит сборку, режим, модели, scores и технические metadata. Старые history snapshots можно импортировать для сравнения; это совместимость данных, а не поддержка старого portable runtime.

## CLI

Версия и диагностика:

```powershell
.\.venv\Scripts\genre-test.exe --version
.\.venv\Scripts\genre-test.exe doctor
```

Один файл:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --view all --full-path
```

Каталог:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music" --mode auto --semantic auto --view all --full-path
```

Validation:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --compare-modes --filter all
```

## Большой regression-прогон

Для большой локальной музыкальной базы есть отдельный runner:

```powershell
cd C:\GIT\Genre_test
.\scripts\run-large-regression.ps1 -Source "D:\Music\BASE"
```

Он выполняет Runtime gate, полный ensemble batch и history recheck. Результаты складываются в timestamped каталог:

```text
results\large_regression\YYYYMMDD_HHMMSS\
```

Полная проверка Fast + Auto + Accurate:

```powershell
.\scripts\run-large-regression.ps1 -Source "D:\Music\BASE" -FullValidation
```

Для очень большой базы сначала рекомендуется обычный Auto batch, затем полный `-FullValidation` только после проверки времени/VRAM и качества результатов.

## Производительность

На проверенном RTX 5070 Ti / CUDA 13.0 MAEST и AST работают на GPU. В release regression v0.4.0 каталог 25/25 завершился без ошибок и с semantic profile 25/25.

`PERF {json}` события в основном логе содержат timing для:

```text
analyzer_init
maest_batch
track
semantic_init
semantic_batch
semantic_track
analysis_item
analysis_session
validation_session
```

## Известные ограничения v0.4.0

- semantic tags — вероятностное evidence, не ground truth;
- mode convergence показывает воспроизводимость, но не доказывает жанровую правильность;
- short-input и близкие Top-1/Top-2 жанры требуют отдельной ambiguity calibration;
- xLaunge остаётся зарегистрированным mode-convergence case;
- короткий 3:2 tempo-case требует независимой ground-truth BPM разметки;
- MAEST и AST пока декодируют semantic audio раздельно — shared decode/cache запланирован;
- Classical требует отдельного period/style resolver;
- XLSX catalog и musical similarity находятся в roadmap.

## Документация

- [`docs/ACTIVE_CURRENT.md`](docs/ACTIVE_CURRENT.md) — фактическое текущее состояние;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — архитектура;
- [`docs/GPU_RUNTIME_0.4.md`](docs/GPU_RUNTIME_0.4.md) — GPU/CUDA runtime;
- [`docs/MODELS.md`](docs/MODELS.md) — pinned models;
- [`docs/VALIDATION_LAB.md`](docs/VALIDATION_LAB.md) — Validation;
- [`docs/RUNTIME_DATA.md`](docs/RUNTIME_DATA.md) — локальные данные;
- [`ROADMAP.md`](ROADMAP.md) — дальнейшие задачи;
- [`RELEASE_NOTES_0.4.0.md`](RELEASE_NOTES_0.4.0.md) — release notes.

## Принцип проекта

Genre_test должен отличать три понятия:

1. **что модель предсказала**;
2. **насколько это стабильно повторяется**;
3. **насколько это музыкально правильно по ground truth**.

Validation решает пункт 2. Для пункта 3 нужна независимая размеченная база и ручная/экспертная проверка.
