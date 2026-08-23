# Genre_test

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
- `bpm`
- `key`
- `mode`
- `audio_features`
- технической информацией о модели и окнах

В `batch` дополнительно создаётся `summary.csv`.

## Репозиторий / безопасность

Вес модели не хранится в Git. `trust_remote_code=True` требуется MAEST-модели Transformers; используйте только зафиксированный доверенный `model_id`. Для строгой воспроизводимости можно указать `--revision <commit>`.

## Лицензирование модели

Код этого проекта — MIT. Лицензия ML-модели задаётся её авторами отдельно и не меняется лицензией репозитория. Перед коммерческим развёртыванием проверяйте model card/условия MTG для конкретной версии MAEST.

## Состояние

См. `docs/ACTIVE_CURRENT.md` и `docs/ROADMAP.md`.
