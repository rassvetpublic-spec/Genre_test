# Releases

В этой папке хранится **только актуальный поддерживаемый portable-релиз** Genre_test.

Текущая линия: **v0.4.x**.

После merge release/cleanup workflow автоматически обновляет:

```text
Genre_test_0.4.0_portable.zip
SHA256SUMS.txt
```

Источник истины для публикации — GitHub Release `v0.4.0`; копия в `releases/` предназначена для удобного доступа непосредственно из репозитория.

Старые portable 0.3.x удалены из active repository и launcher/runtime больше их не поддерживает. Исторические commits/tags могут оставаться только как Git history.

Перед использованием ZIP сверяйте SHA-256 со значением в `SHA256SUMS.txt`.
