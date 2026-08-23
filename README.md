# Genre_test

**Current version: 0.2.0**

Локальный анализатор музыкального жанра для Windows/Linux.

## Что делает MVP

- анализирует WAV/FLAC/MP3/OGG/M4A/AAC (форматы зависят от backend `soundfile`/`audioread`);
- режет длинный трек на репрезентативные 30-секундные окна;
- запускает MTG **MAEST Discogs 519** через Hugging Face Transformers;
- агрегирует Top-N стилей между окнами;
- строит более широкий `primary_genre` по иерархии `Genre---Style`;
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

## Genre resolver v0.2

Помимо сырого `primary_genre`, JSON теперь содержит:

- `resolved_genre` — человекочитаемый основной стиль;
- `classification` — `primary` или `hybrid`;
- `confidence`;
- `family_margin`;
- `secondary_genre`.

Raw `top_styles` и `broad_genres` сохраняются без потери.

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
- `secondary_genre`
- `audio_features`
- технической информацией о модели и окнах

В `batch` дополнительно создаётся `summary.csv`.

## Репозиторий / безопасность

Вес модели не хранится в Git. `trust_remote_code=True` требуется MAEST-модели Transformers; используйте только зафиксированный доверенный `model_id`. Для строгой воспроизводимости можно указать `--revision <commit>`.

## Лицензирование модели

Код этого проекта — MIT. Лицензия ML-модели задаётся её авторами отдельно и не меняется лицензией репозитория. Перед коммерческим развёртыванием проверяйте model card/условия MTG для конкретной версии MAEST.

## Состояние

См. `docs/ACTIVE_CURRENT.md` и `docs/ROADMAP.md`.

## Python prerequisite

Genre_test requires **Python 3.11 or 3.12 x64**. On Windows the recommended version is Python 3.12.

If Python is not installed, run:

```powershell
.\scripts\setup.ps1 -InstallPython
```

The setup script can install Python 3.12 through `winget`, recovers from an incomplete `.venv`, and then installs the project dependencies.
