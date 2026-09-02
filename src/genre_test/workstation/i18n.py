from __future__ import annotations

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = ("ru", "en")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "Genre_test Workstation",
        "app.subtitle": "Local-first studio workspace",
        "nav.project": "Project",
        "nav.analyze": "Analyze",
        "nav.catalog": "Catalog",
        "nav.search": "Search",
        "nav.repair": "Repair",
        "nav.stems": "Stems",
        "nav.master": "Master",
        "nav.compare": "Compare",
        "nav.delivery": "Delivery",
        "nav.settings": "Settings",
        "status.local": "Local workstation",
        "status.ready": "Shell ready",
        "status.na": "N/A",
        "panel.project.title": "Project",
        "panel.project.body": "Source and derived-asset navigation arrives through canonical project services.",
        "panel.runtime.title": "Runtime",
        "panel.runtime.cpu": "CPU",
        "panel.runtime.ram": "RAM",
        "panel.runtime.gpu": "GPU",
        "panel.runtime.vram": "VRAM",
        "panel.runtime.temperature": "Temperature",
        "panel.runtime.refresh": "Refresh runtime",
        "panel.capabilities.title": "Capabilities",
        "panel.capabilities.body": "P1 exposes the shell and typed seams. Domain surfaces stay deferred until their owning phases.",
        "settings.language": "Language",
        "settings.language.ru": "Russian",
        "settings.language.en": "English",
        "footer.api": "Workstation API",
        "error.runtime": "Runtime telemetry is unavailable",
        "error.request": "Request failed",
    },
    "ru": {
        "app.title": "Genre_test Workstation",
        "app.subtitle": "Локальная студийная рабочая среда",
        "nav.project": "Проект",
        "nav.analyze": "Анализ",
        "nav.catalog": "Каталог",
        "nav.search": "Поиск",
        "nav.repair": "Ремонт",
        "nav.stems": "Стемы",
        "nav.master": "Мастер",
        "nav.compare": "Сравнение",
        "nav.delivery": "Доставка",
        "nav.settings": "Настройки",
        "status.local": "Локальная рабочая станция",
        "status.ready": "Оболочка готова",
        "status.na": "Н/Д",
        "panel.project.title": "Проект",
        "panel.project.body": "Навигация по источнику и производным ассетам подключается через канонические сервисы проекта.",
        "panel.runtime.title": "Ресурсы",
        "panel.runtime.cpu": "ЦП",
        "panel.runtime.ram": "ОЗУ",
        "panel.runtime.gpu": "ГП",
        "panel.runtime.vram": "Видеопамять",
        "panel.runtime.temperature": "Температура",
        "panel.runtime.refresh": "Обновить ресурсы",
        "panel.capabilities.title": "Возможности",
        "panel.capabilities.body": "P1 даёт оболочку и типизированные точки подключения. Предметные экраны остаются за своими фазами.",
        "settings.language": "Язык",
        "settings.language.ru": "Русский",
        "settings.language.en": "Английский",
        "footer.api": "Workstation API",
        "error.runtime": "Телеметрия ресурсов недоступна",
        "error.request": "Ошибка запроса",
    },
}


def validate_catalog() -> None:
    baseline = set(TRANSLATIONS["en"])
    for language in SUPPORTED_LANGUAGES:
        current = set(TRANSLATIONS[language])
        if current != baseline:
            missing = sorted(baseline - current)
            extra = sorted(current - baseline)
            raise RuntimeError(
                f"workstation translation catalog mismatch for {language}: "
                f"missing={missing}, extra={extra}"
            )


def normalize_language(language: str | None) -> str:
    value = (language or DEFAULT_LANGUAGE).strip().lower()
    if value not in SUPPORTED_LANGUAGES:
        return DEFAULT_LANGUAGE
    return value


def catalog(language: str | None) -> dict[str, str]:
    validate_catalog()
    selected = normalize_language(language)
    english = TRANSLATIONS["en"]
    localized = TRANSLATIONS.get(selected, {})
    return {key: localized.get(key, english.get(key, key)) for key in english}


def translate(language: str | None, key: str) -> str:
    selected = normalize_language(language)
    return TRANSLATIONS.get(selected, {}).get(key, TRANSLATIONS["en"].get(key, key))
