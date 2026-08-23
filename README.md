# Genre_test

**Current version: 0.2.1**

Локальный анализатор музыкального жанра для Windows/Linux.

## Что делает MVP

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC;
- запускает MTG **MAEST Discogs 519** через Hugging Face Transformers;
- автоматически выбирает репрезентативные 30-секундные окна по длительности и уверенности результата;
- агрегирует Top-N стилей между окнами;
- строит более широкий `primary_genre` по иерархии `Genre---Style`;
- рассчитывает человекочитаемый `resolved_genre` и evidence-aware confidence;
- оценивает BPM, примерный key/mode, RMS, spectral centroid, rolloff, zero-crossing rate;
- пишет JSON и CSV;
- умеет анализировать один файл или каталог пакетно.

> Жанровая классификация вероятностная. Итог — подсказка для редактора/дистрибьютора, а не абсолютная истина.

## Windows GUI

После установки:

```powershell
.\scripts\gui.ps1
```

или двойным кликом:

```text
scripts\Genre_test_GUI.cmd
```

Обычный GUI показывает только действительно нужные настройки:

- входной файл/папка;
- папка результатов;
- `Device`: `auto / cuda / cpu`;
- `Режим анализа`: `Авто / Быстрый / Точный / Экспертный`.

`Окон` и `Top-K` скрыты и появляются только в режиме `Экспертный`.

### Режимы анализа

**Авто** — режим по умолчанию. Максимальное число окон выбирается по длительности:

| Длительность | Максимум окон |
|---:|---:|
| < 60 с | 1 |
| 60–120 с | 3 |
| 120–210 с | 5 |
| 210–300 с | 7 |
| 300–420 с | 9 |
| > 420 с | 11 |

Для длинного трека Auto сначала анализирует 5 равномерно распределённых окон. Если результат уже `primary + high confidence`, анализ останавливается. Если результат hybrid/ambiguous, модель автоматически дозаполняет окна до duration-based target.

**Быстрый** — максимум 3 окна.

**Точный** — всегда использует полный duration-based target без ранней остановки.

**Экспертный** — ручное число окон и Top-K.

Внутренне classifier получает минимум Top-25 кандидатов даже при стандартном отчёте Top-15, чтобы resolver видел конкурирующие стили.

## Genre resolver v0.2.1

Resolver сохраняет сырые MAEST probabilities и добавляет отдельный человекочитаемый слой.

Основные поля:

- `resolved_genre` — основной fine-style;
- `classification` — `primary` или `hybrid`;
- `confidence` — учитывает и broad-family evidence, и конкуренцию fine styles;
- `family_margin` — абсолютная разница между двумя ведущими broad families;
- `family_ratio` — отношение score второй broad family к первой;
- `style_margin` — относительный отрыв resolved style от сильнейшего конкурирующего style;
- `secondary_genre` — вторая broad family;
- `secondary_style` — сильнейший альтернативный fine-style;
- `analysis_mode` — использованный режим;
- `windows_analyzed` — фактически проанализированное число окон.

Hybrid определяется не только абсолютным family margin, но и относительной близостью broad families. Generic labels вроде `Pop---Ballad` и `Pop---Vocal` получают контекст (`Pop Ballad`, `Vocal Pop`).

Raw `top_styles` и `broad_genres` сохраняются без потери и остаются источником истины для повторной калибровки resolver.

## Модель

По умолчанию:

`mtg-upf/discogs-maest-30s-pw-129e-519l`

Модель загружается при первом запуске с Hugging Face и затем используется из локального кеша.

## Быстрый старт — Windows PowerShell 7

```powershell
cd C:\GIT\Genre_test
.\scripts\setup.ps1
```

Скрипт автоматически выбирает CUDA 12.8 wheel PyTorch при обнаружении NVIDIA GPU. Для CPU-only: `./scripts/setup.ps1 -Cpu`.

Стандартный Auto-анализ:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --out ".\results"
```

Точный режим:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --mode accurate
```

Экспертный режим:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --mode expert --windows 9 --top-k 20
```

Папка целиком:

```powershell
.\.venv\Scripts\genre-test.exe batch "D:\Music\Album" --out ".\results"
```

Принудительно CPU:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --device cpu
```

CUDA:

```powershell
.\.venv\Scripts\genre-test.exe doctor
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --device cuda
```

## Выход

Для каждого файла создаётся JSON с:

- `primary_genre`
- `primary_genre_score`
- `top_styles`
- `broad_genres`
- `resolved_genre`
- `classification`
- `confidence`
- `family_margin`
- `family_ratio`
- `style_margin`
- `secondary_genre`
- `secondary_style`
- `analysis_mode`
- `windows_analyzed`
- `audio_features`
- технической информацией о модели

В `batch` дополнительно создаётся `summary.csv`.

## Репозиторий / безопасность

Вес модели не хранится в Git. `trust_remote_code=True` требуется MAEST-модели Transformers; используйте только доверенный `model_id`. Для строгой воспроизводимости можно указать `--revision <commit>`.

Аудио/видео и generated `results/` не должны храниться в репозитории.

## Лицензирование модели

Код этого проекта — MIT. Лицензия ML-модели задаётся её авторами отдельно и не меняется лицензией репозитория.

## Состояние

См. `docs/ACTIVE_CURRENT.md`, `docs/ROADMAP.md` и `docs/VALIDATION_BASELINE.md`.

## Python prerequisite

Genre_test requires **Python 3.11 or 3.12 x64**. On Windows the recommended version is Python 3.12.

If Python is not installed, run:

```powershell
.\scripts\setup.ps1 -InstallPython
```
