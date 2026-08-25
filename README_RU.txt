Genre_test 0.4.0 Portable — русская инструкция
=============================================

АКТУАЛЬНЫЙ РЕЛИЗ
----------------
Поддерживаемая portable-линия: 0.4.x.
Старые portable 0.3.x выведены из эксплуатации и не используются активным launcher/runtime.

ЧТО ЭТО
-------
Genre_test — локальный музыкальный анализатор для Windows.
Основной профиль строится как ансамбль:

- MAEST Discogs519 — detailed genre/style;
- AudioSet AST — independent semantic evidence;
- DSP/librosa — BPM, key и технические свойства исходного аудио.

GUI показывает три представления одного результата:

- Обычный;
- SUNO;
- Дистрибьютор.

Также доступны отдельные вкладки Validation и Проверка сохранённых сборок.

ГДЕ ВЗЯТЬ
---------
Актуальный архив:

   Genre_test_0.4.0_portable.zip

Он публикуется:

1. в GitHub Release v0.4.0;
2. в папке releases репозитория.

Рядом находится SHA256SUMS.txt для проверки архива.

БЫСТРЫЙ СТАРТ
-------------
1. Распакуйте ZIP в обычную локальную папку.
2. Не запускайте программу прямо из ZIP.
3. Рекомендуется короткий путь без сетевых дисков, например:

   C:\Genre_test_0.4.0_portable

4. Запустите:

   Genre_test_START.cmd

5. На первом запуске требуется интернет.

Фиксированный путь больше НЕ обязателен: portable можно распаковать в другой обычный локальный каталог.

ЧТО ДЕЛАЕТ ПЕРВЫЙ ЗАПУСК
------------------------
Packaged release использует штатный Windows PowerShell 5.1 и scripts\release_bootstrap.ps1.
PowerShell 7 заранее не требуется.

Launcher автоматически проверяет/подготавливает:

- WinGet / App Installer;
- официальный WinGet repair через Microsoft.WinGet.Client при необходимости;
- Microsoft Visual C++ 2015–2022 x64 Runtime;
- Python 3.11 / 3.12 / 3.13 x64;
- Python 3.12 x64 как fallback, если совместимого Python нет;
- отдельный .venv внутри папки Genre_test;
- PyTorch 2.12.1;
- NVIDIA route: CUDA 13.0 / cu130;
- native CUDA architecture для Blackwell, включая sm_120;
- CPU PyTorch на настоящих CPU-only системах;
- FFmpeg;
- зависимости Genre_test;
- genre-test --version;
- genre-test doctor;
- запуск GUI после успешной диагностики.

PYTHON
------
Поддерживаются Python 3.11, 3.12 и 3.13 x64.

Если подходящий Python уже установлен, он переиспользуется.
Если ни одного совместимого runtime нет, launcher устанавливает Python 3.12 x64.

PYTORCH / NVIDIA / CPU
----------------------
PyTorch нужен и на CPU, потому что MAEST и AudioSet AST работают через PyTorch.

Для NVIDIA используется PyTorch 2.12.1 + CUDA 13.0 / cu130.
NVIDIA определяется не только через nvidia-smi, но и через Windows PnP/CIM.

Если NVIDIA физически присутствует, но CUDA runtime или native architecture не работают, setup должен завершиться ошибкой. Такой компьютер не маскируется под CPU-only.

На настоящем CPU-only компьютере CPU PyTorch является штатным режимом, а Runtime Health показывает:

   CUDA: N/A | GPU: N/A

Совместимый PyTorch повторно не скачивается без необходимости.
Обычные pip/Hugging Face caches переиспользуются, но чужой project .venv напрямую не подключается.

МОДЕЛИ
------
При первом анализе могут быть скачаны pinned-модели:

MAEST:
   mtg-upf/discogs-maest-30s-pw-129e-519l
   revision 6c35f32a350f74351870937d5ae0bae1d898d1df

AudioSet AST:
   MIT/ast-finetuned-audioset-10-10-0.4593
   revision f826b80d28226b62986cc218e5cec390b1096902

Для публичных pinned-моделей Hugging Face token не обязателен.
Веса моделей в portable ZIP не входят.

GUI
---
Тёмная тема включена по умолчанию.
Справа сверху можно переключить Тёмная / Светлая без перезапуска.

Вкладки:

Анализ
   Обычный анализ файла/папки.

Validation
   Повторный анализ, mode convergence, history drift и регрессионная проверка.

Проверка
   Сравнение уже сохранённых build identity без повторного анализа аудио.

В Expert-режиме видны число MAEST-окон и Top-K.
Safe Stop останавливает пакет после текущего безопасного участка и сохраняет уже завершённые результаты.

HISTORY И ЛОГИ
--------------
Runtime data находятся внутри распакованной папки:

   .genre_test\history.sqlite3
   .genre_test\logs\genre_test.log
   .genre_test\bootstrap.log
   .genre_test\torch_import_diagnostic.txt
   results\

Клик по History в GUI открывает соответствующую папку.

ПОВТОРНЫЙ ЗАПУСК
----------------
Повторно запускайте тот же Genre_test_START.cmd.
Совместимые Python, .venv, PyTorch, FFmpeg и caches переиспользуются.

После создания .venv не рекомендуется переносить всю папку portable в другое место. Сначала выберите конечный каталог, затем выполняйте первый запуск.

ПРОВЕРКА АРХИВА
---------------
Сверьте SHA-256 файла Genre_test_0.4.0_portable.zip со строкой в SHA256SUMS.txt.

СИСТЕМНЫЕ ТРЕБОВАНИЯ
--------------------
- Windows 10 или Windows 11 x64;
- Windows PowerShell 5.1;
- интернет при первой настройке и первом скачивании моделей;
- несколько ГБ свободного места для Python/PyTorch/model cache;
- NVIDIA не обязательна.

ЕСЛИ ЗАПУСК НЕ УДАЛСЯ
---------------------
1. Прочитайте последнюю строку [FAIL] в окне launcher.
2. Откройте:

   .genre_test\bootstrap.log

3. При ошибке PyTorch приложите:

   .genre_test\torch_import_diagnostic.txt

4. После запуска GUI проверьте кнопку Зависимости и строку Runtime Health.

ОЖИДАЕМЫЙ RUNTIME
-----------------
GPU-компьютер с рабочей NVIDIA:

   Runtime: OK | Deps: 12/12 | CUDA: OK | GPU: OK | FFmpeg: OK | HF: OK

CPU-only компьютер:

   Runtime: OK | Deps: 12/12 | CUDA: N/A | GPU: N/A | FFmpeg: OK | HF: OK

ВЕРСИЯ
------
Genre_test 0.4.0 Portable Release
