Genre_test 0.3.6 Portable — инструкция
=====================================

ЧТО ЭТО
-------
Genre_test — локальный анализатор музыкального жанра для Windows.
Этот portable prerelease собран так, чтобы на другом компьютере не требовалось вручную настраивать Python, виртуальное окружение, PyTorch, FFmpeg или WinGet.

ВАЖНО: КУДА РАСПАКОВЫВАТЬ
-------------------------
ZIP нужно распаковать ПРЯМО В КОРЕНЬ ДИСКА C:\.

После распаковки рабочая папка обязана быть:

   C:\Genre_test_0.3.6_portable

А запускаемый файл должен находиться здесь:

   C:\Genre_test_0.3.6_portable\Genre_test_START.cmd

Не запускайте пакет из Downloads, Рабочего стола, D:\, сетевой папки или прямо внутри ZIP.
Это обязательное условие prerelease 0.3.6: фиксированный ASCII-путь исключает проблемы Windows/PyTorch с DLL и путями, содержащими кириллицу.

БЫСТРЫЙ СТАРТ
-------------
1. Сохраните ZIP на компьютер.

2. Распакуйте ZIP прямо в:

   C:\

В результате должна появиться папка:

   C:\Genre_test_0.3.6_portable

3. На первом запуске компьютер должен быть подключён к интернету.

4. Дважды щёлкните:

   C:\Genre_test_0.3.6_portable\Genre_test_START.cmd

5. Ничего дополнительно вводить не нужно. Скрипт автоматически:
   - проверит, что пакет запущен именно из C:\Genre_test_0.3.6_portable
   - использует штатный Windows PowerShell 5.1; PowerShell 7 не требуется
   - проверит Windows x64
   - проверит Windows Package Manager (winget)
   - если winget отсутствует, попытается автоматически восстановить его официальным методом Microsoft через Microsoft.WinGet.Client и Repair-WinGetPackageManager
   - если автоматическое восстановление winget не удалось, откроет App Installer в Microsoft Store как последний fallback
   - проверит Microsoft Visual C++ 2015–2022 x64 Runtime и при необходимости установит его
   - найдёт подходящий Python 3.11/3.12 x64
   - при отсутствии установит Python 3.12 через winget
   - создаст локальное окружение .venv внутри C:\Genre_test_0.3.6_portable
   - определит наличие NVIDIA GPU
   - установит PyTorch CUDA 12.8 для NVIDIA либо CPU-версию PyTorch
   - проверит реальный import PyTorch
   - найдёт FFmpeg
   - при отсутствии установит Gyan.FFmpeg через winget
   - установит зависимости Genre_test
   - выполнит Runtime Health
   - выполнит genre-test --version
   - выполнит genre-test doctor
   - после успешной диагностики автоматически запустит GUI

6. При первом анализе аудио программа может скачать модель MAEST с Hugging Face. Это нормально. Модель затем хранится в локальном кэше проекта и повторно обычно не скачивается.

ПОВТОРНЫЙ ЗАПУСК
----------------
В дальнейшем снова запускайте только:

   C:\Genre_test_0.3.6_portable\Genre_test_START.cmd

Уже установленный WinGet, VC++ Runtime, Python, .venv, PyTorch и FFmpeg будут переиспользованы после проверки, поэтому повторный запуск заметно быстрее.

СИСТЕМНЫЕ ТРЕБОВАНИЯ
--------------------
- Windows 10 или Windows 11 x64
- штатный Windows PowerShell 5.1
- интернет на первом запуске
- желательно не менее 8 ГБ свободного места на диске C: перед первой установкой

PowerShell 7 / pwsh заранее устанавливать не нужно.
NVIDIA не обязательна. Без NVIDIA программа автоматически использует CPU PyTorch, но анализ будет медленнее.
В зависимости от политики Windows отдельная системная установка может запросить подтверждение UAC.

ЕСЛИ НЕТ WINGET
---------------
Это предусмотрено.

Genre_test_START.cmd сначала пытается найти winget обычным способом и внутри установленного App Installer.
Если winget действительно отсутствует или повреждён, запускается официальный путь восстановления Microsoft:

   Install-PackageProvider NuGet
   Install-Module Microsoft.WinGet.Client
   Repair-WinGetPackageManager -Force -Latest

После восстановления скрипт повторно ищет winget и продолжает установку автоматически.

Только если официальный repair не сработал, скрипт открывает страницу App Installer в Microsoft Store.

PYTORCH / DLL
-------------
Перед установкой PyTorch скрипт проверяет Microsoft Visual C++ 2015–2022 x64 Runtime.
Это системная зависимость PyTorch на Windows.

Если import torch всё равно завершится ошибкой, launcher сохранит полный текст ошибки в:

   C:\Genre_test_0.3.6_portable\.genre_test\torch_import_diagnostic.txt

и добавит его в bootstrap.log.

ДИАГНОСТИКА
-----------
Лог первоначальной настройки:

   C:\Genre_test_0.3.6_portable\.genre_test\bootstrap.log

Диагностика импорта PyTorch:

   C:\Genre_test_0.3.6_portable\.genre_test\torch_import_diagnostic.txt

Основной лог программы:

   C:\Genre_test_0.3.6_portable\.genre_test\logs\genre_test.log

В GUI также есть кнопка «Зависимости...», где отображается состояние Python, библиотек, CUDA/GPU, FFmpeg, HF auth и MAEST.

ЕСЛИ ЗАПУСК НЕ УДАЛСЯ
---------------------
1. Не закрывайте окно с ошибкой сразу — прочитайте строку [FAIL].
2. Проверьте, что папка программы называется точно:

   C:\Genre_test_0.3.6_portable

3. Откройте:

   .genre_test\bootstrap.log

4. Если ошибка связана с PyTorch, приложите также:

   .genre_test\torch_import_diagnostic.txt

5. Передайте эти файлы разработчику.

ВАЖНО
-----
- ZIP распаковывается непосредственно в C:\.
- Итоговая папка: C:\Genre_test_0.3.6_portable.
- Не запускайте программу прямо из ZIP.
- Не переносите только один CMD-файл отдельно от остальных файлов программы.
- Папка .venv создаётся внутри C:\Genre_test_0.3.6_portable и относится только к Genre_test.
- Первый запуск может занять заметное время: скачиваются Python/PyTorch/FFmpeg и позднее модель MAEST.
- Аудиофайлы не отправляются в сторонний облачный сервис для жанрового анализа; основной анализ выполняется локально.

ВЕРСИЯ
------
Genre_test 0.3.6 Portable prerelease
Исходная стабильная база: main commit 06afdc5cb4d940797e514873e34b737ef0250540
