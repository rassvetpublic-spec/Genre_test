# Genre_test

**Current version: 0.4.0**

Локальный музыкальный анализатор для Windows/Linux. В v0.4 основной пользовательский профиль строится как ансамбль **MAEST Discogs519 + AudioSet AST**, а Validation Lab сохраняет стабильный raw-MAEST контур для сравнения с накопленной историей 0.3.x.

## Что выдаёт v0.4

Обычный анализ формирует `AudioProfile`:

- primary genre / broad family;
- confidence;
- secondary influence;
- adjacent genres;
- mood tags;
- vocal tags;
- instrumentation;
- production/electronic tags;
- BPM и key/mode;
- distributor genre/subgenre;
- SUNO Style of Music;
- ensemble agreement и evidence metadata в JSON/CSV.

Жанровый fine-style эксперт — MAEST Discogs519. Независимый semantic слой — MIT Audio Spectrogram Transformer, fine-tuned on AudioSet. Semantic слой используется как дополнительное evidence, а не как безусловная замена MAEST.

## Архитектура 0.4

```text
Audio
  |
  +--> MAEST Discogs519 --------------------+
  |    fine styles / broad families         |
  |                                         +--> Evidence fusion
  +--> AudioSet AST ------------------------+       |
  |    genre / vocal / instruments / mood           v
  |                                             AudioProfile
  +--> librosa / DSP                                 |
       BPM / key / spectral features                 +--> Normal
                                                     +--> SUNO
                                                     +--> Distributor

Raw MAEST -----------------------------------------> Validation Lab
```

### Ensemble policy

MAEST остаётся главным источником detailed genre/style. AudioSet AST добавляет независимое broad-family и semantic evidence.

- high-confidence MAEST family не переопределяется semantic-моделью;
- при неоднозначном MAEST fused evidence может изменить broad family;
- если family меняется, выбирается strongest MAEST fine style внутри новой family;
- disagreement моделей понижает итоговую confidence;
- если semantic-модель недоступна, режим `auto` продолжает работу как MAEST-only и фиксирует fallback в metadata/log.

## Модели и воспроизводимость

### MAEST Discogs519

```text
model:    mtg-upf/discogs-maest-30s-pw-129e-519l
revision: 6c35f32a350f74351870937d5ae0bae1d898d1df
```

### AudioSet AST

```text
model:    MIT/ast-finetuned-audioset-10-10-0.4593
revision: f826b80d28226b62986cc218e5cec390b1096902
```

Semantic profile использует до трёх распределённых 10-секундных окон. Модель загружается лениво при первом обычном анализе и использует тот же PyTorch/CUDA runtime.

Result schema: **4**.

## Windows GUI

Запуск:

```powershell
.\scripts\gui.ps1
```

или:

```text
scripts\Genre_test_GUI.cmd
```

GUI имеет две вкладки:

```text
Анализ
Validation / Перепроверка
```

Обычный Analysis выводит результат по мере обработки треков. В нём скрыты внутренние `run_id`, `track_id`, hashes и model revisions. Полная техническая информация остаётся в Validation и JSON/history.

Текст можно выделять мышью и копировать `Ctrl+C`, `Ctrl+Insert`; `Ctrl+A` выделяет всё. Поддерживается русская раскладка Windows. Кнопка `СКОПИРОВАТЬ СОДЕРЖИМОЕ` копирует весь отчёт.

### Представления результата

В обычном Analysis доступны:

```text
Обычный
SUNO
Дистрибьютор
```

`Обычный` показывает жанровый профиль, semantic tags, tempo/key и объединённую таблицу Top styles + Broad families.

`SUNO` формирует компактный `Style of Music` из primary genre, influence, mood, vocal, instrumentation, BPM и key.

`Дистрибьютор` выдаёт broad distributor genre, subgenre, primary genre и соседние влияния.

## Runtime Health

Верхняя строка GUI показывает компактный статус:

```text
Runtime: OK | Deps: 12/12 | CUDA: OK | FFmpeg: OK | HF: OK
```

Кнопка `Зависимости…` открывает полный список Python/packages/CUDA/GPU/FFmpeg/HF auth и pinned model revisions.

Основная строка GUI показывает только:

```text
Genre_test 0.4.0 | Models: MAEST Discogs519 + AudioSet AST
```

Полные hashes/revisions находятся только в диагностическом окне.

## Режимы MAEST

| Режим | Поведение |
|---|---|
| Auto | основной режим; начинает с достаточного минимума и расширяется при неоднозначности |
| Fast | максимум 3 репрезентативных окна |
| Accurate | полный duration-based target |
| Expert | ручные окна и Top-K |

Duration target:

| Длительность | Максимум MAEST-окон |
|---:|---:|
| < 60 с | 1 |
| 60–120 с | 3 |
| 120–210 с | 5 |
| 210–300 с | 7 |
| 300–420 с | 9 |
| > 420 с | 11 |

Для длинного трека Auto сначала анализирует 5 распределённых окон. Если получен стабильный `primary + high confidence`, он останавливается. Иначе расширяется до полного target.

На CUDA MAEST объединяет независимые окна в GPU batch до 8 окон. При CUDA OOM batch автоматически уменьшается вдвое.

## Input QC

```text
< 10 s   -> INSUFFICIENT_AUDIO
            genre verdict отсутствует
            MAEST/semantic inference не выполняется

10-30 s  -> SHORT_INPUT
            одно padded MAEST window
            confidence не выше medium

>= 30 s  -> NORMAL
```

Для `<10 s` используется warning-free lightweight DSP path без beat/chroma вычислений.

## Validation Lab

Validation специально остаётся raw-MAEST диагностическим контуром. Это сохраняет сопоставимость с историей 0.3.x и не смешивает изменение жанрового ядра с новым semantic-profile слоем.

Validation отвечает на три вопроса:

1. сходятся ли Fast / Auto / Accurate;
2. изменился ли raw жанровый результат между версиями;
3. какие треки требуют ручной проверки.

В Validation доступны полные:

- `run_id` / `track_id`;
- analyzer/schema/version;
- MAEST model/revision/device;
- raw score vectors;
- convergence/history drift;
- NOT_COMPARABLE semantics;
- если enriched result присутствует в истории — semantic/profile metadata.

### Track identity и history

```text
track_id = sha256:<content hash>
```

Переименование/перенос не создаёт новый logical track. SQLite хранится здесь:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
```

Runtime data:

```text
.genre_test\history.sqlite3
.genre_test\logs\genre_test.log
.genre_test\huggingface\
results\
```

## Performance telemetry

Лог содержит machine-readable `PERF {json}` события, включая:

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

MAEST telemetry хранит load/features/inference timing, GPU batches, cache reuse и realtime speed. Semantic telemetry отдельно показывает загрузку AST и inference по semantic windows.

## FFmpeg bootstrap

На Windows `setup.ps1` и `upgrade.ps1`:

1. ищут FFmpeg в PATH, WinGet Links, Scoop, Chocolatey и стандартных каталогах;
2. при отсутствии устанавливают `Gyan.FFmpeg` через WinGet;
3. добавляют найденный путь в текущий процесс;
4. `doctor` показывает фактический путь и AAC/M4A fallback status.

```powershell
.\scripts\ensure_ffmpeg.ps1
```

Отключить auto-install:

```powershell
.\scripts\setup.ps1 -SkipFFmpeg
.\scripts\upgrade.ps1 -SkipFFmpeg
```

## Hugging Face cache/auth

Genre_test не переопределяет пользовательский `HF_HOME`, поэтому token из `hf auth login` остаётся доступен. Repo-local используются только model caches:

```text
HF_HUB_CACHE -> .genre_test\huggingface\hub
HF_XET_CACHE -> .genre_test\huggingface\xet
```

## CLI

Версия:

```powershell
.\.venv\Scripts\genre-test.exe --version
```

Runtime diagnostics:

```powershell
.\.venv\Scripts\genre-test.exe doctor
```

Обычный ensemble profile:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav"
```

SUNO output:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --view suno
```

Distributor output:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --view distributor
```

Отключить independent semantic model:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --semantic off
```

Требовать semantic layer без fallback:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --semantic on
```

Batch:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music\Album"
```

Raw MAEST Validation:

```powershell
.\.venv\Scripts\genre-test.exe validate "D:\Music" --compare-modes
```

## Реальный baseline до 0.4

Последний полный v0.3.5 Auto catalog run:

```text
187 paths
187 processed
0 errors
~24.3 tracks/min
```

На 180 сопоставленных unique tracks переход 0.3.4 -> 0.3.5 дал 180/180 совпадений resolved genre, broad family, classification, confidence и windows. Это raw-MAEST baseline, относительно которого проверяется 0.4.

## Ограничения 0.4.0

- AudioSet semantic tags являются вероятностным independent evidence, а не ground truth.
- `SUNO Style of Music` и distributor mapping — deterministic presentation layer, а не утверждение о требованиях конкретного дистрибьютора.
- Validation 0.4.0 пока валидирует raw MAEST, а не calibration semantic-fusion layer.
- Semantic analyzer сейчас повторно декодирует аудио после MAEST; shared-decode optimization запланирована в 0.4.x.
- track-to-track musical similarity, XLSX catalog export и calibrated danceability/acoustic scores вынесены в roadmap.

См. [ROADMAP.md](ROADMAP.md).
