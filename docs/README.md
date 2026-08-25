# Genre_test documentation

Актуальная документация описывает поддерживаемую линию **v0.4.x**.

1. [`../README.md`](../README.md) — основной README и быстрый вход.
2. [`ACTIVE_CURRENT.md`](ACTIVE_CURRENT.md) — фактическое текущее состояние продукта.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — MAEST + AudioSet AST + DSP + AudioProfile.
4. [`GPU_RUNTIME_0.4.md`](GPU_RUNTIME_0.4.md) — Python / PyTorch / CUDA / Blackwell runtime.
5. [`MODELS.md`](MODELS.md) — pinned model ids и revisions.
6. [`VALIDATION_LAB.md`](VALIDATION_LAB.md) — Validation, history drift и build comparison.
7. [`RUNTIME_DATA.md`](RUNTIME_DATA.md) — SQLite, logs, caches и results.
8. [`SAFE_STOP.md`](SAFE_STOP.md) — Safe Stop semantics.
9. [`../ROADMAP.md`](../ROADMAP.md) — единственный актуальный roadmap.

## Правило актуальности

Активная продуктовая документация описывает v0.4.x. Старые portable/runtime инструкции 0.3.x удалены из активного дерева. Исторические данные при необходимости остаются доступны через Git history и импорт старых result snapshots в Validation.
