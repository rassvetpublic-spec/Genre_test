# Genre_test

**Current version: 0.2.1**

Локальный анализатор музыкального жанра для Windows/Linux.

## Что делает MVP

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC (форматы зависят от backend `soundfile`/`audioread`);
- режет длинный трек на репрезентативные 30-секундные окна;
- запускает MTG **MAEST Discogs 519** через Hugging Face Transformers;
- агрегирует Top-N стилей между окнами;
- строит более широкий `primary_genre` по иерархии `Genre---Style`;
- рассчитывает человекочитаемый `resolved_genre` и evidence-aware confidence;
- оценивает BPM, примерный key/mode, RMS, spectral centroid, rolloff, zero-crossing rate;
- пишет JSON и CSV;
- умеет анализировать один файл или каталог пакетно.

> Жанровая классификация вероятностная. Итог — подсказка для редактора/дистрибьютора, а не абсолютная истина.

## Windows GUI

После установки можно запускать без ручного ввода путей:

```powershell
.\scripts\gui.ps1
```

или двойным кликом:

```text
scripts\Genre_test_GUI.cmd
```

GUI позволяет:

- выбрать аудиофайл стандартным Windows-окном;
- выбрать целую папку для batch-анализа;
- выбрать папку результатов;
- переключить `auto / cuda / cpu`;
- задать число окон и Top-K;
- видеть итоговый `resolved genre`, confidence, hybrid/primary, BPM/key и Top styles;
- открыть папку результатов одной кнопкой.

CLI остаётся полностью доступным.

## Genre resolver v0.2.1

Resolver сохраняет сырые MAEST probabilities и добавляет отдельный человекочитаемый слой.

Основные поля:

- `resolved_genre` — основной fine-style;
- `classification` — `primary` или `hybrid`;
- `confidence` — учитывает и broad-family evidence, и конкуренцию fine styles;
- `family_margin` — абсолютная разница между двумя ведущими broad families;
- `family_ratio` — отношение score второй broad family к первой;
- `style_margin` — относительный отрыв resolved style от сильнейшего конкурирующего style в двух ведущих broad families; отрицательное значение означает, что strongest competing style имеет больший score;
- `secondary_genre` — вторая broad family;
- `secondary_style` — сильнейший альтернативный fine-style.

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

После установки:

```powershell
.\.venv\Scripts\genre-test.exe analyze "D:\Music\track.wav" --out ".\results"
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
- `audio_features`
- технической информацией о модели и окнах

В `batch` дополнительно создаётся `summary.csv`.

## Репозиторий / безопасность

Вес модели не хранится в Git. `trust_remote_code=True` требуется MAEST-модели Transformers; используйте только зафиксированный доверенный `model_id`. Для строгой воспроизводимости можно указать `--revision <commit>`.

Аудио/видео и generated `results/` не должны храниться в репозитории.

## Лицензирование модели

Код этого проекта — MIT. Лицензия ML-модели задаётся её авторами отдельно и не меняется лицензией репозитория. Перед коммерческим развёртыванием проверяйте model card/условия MTG для конкретной версии MAEST.

## Состояние

См. `docs/ACTIVE_CURRENT.md`, `docs/ROADMAP.md` и `docs/VALIDATION_BASELINE.md`.

## Python prerequisite

Genre_test requires **Python 3.11 or 3.12 x64**. On Windows the recommended version is Python 3.12.

If Python is not installed, run:

```powershell
.\scripts\setup.ps1 -InstallPython
```

The setup script can install Python 3.12 through `winget`, recovers from an incomplete `.venv`, and then installs the project dependencies.
