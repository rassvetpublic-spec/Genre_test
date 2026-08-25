# Genre_test documentation

Актуальная документация v0.4 организована так:

1. [`../README.md`](../README.md) — основной русскоязычный README и быстрый вход.
2. [`ACTIVE_CURRENT.md`](ACTIVE_CURRENT.md) — фактическое текущее состояние продукта.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — архитектура MAEST + AST + DSP + AudioProfile.
4. [`GPU_RUNTIME_0.4.md`](GPU_RUNTIME_0.4.md) — Python/PyTorch/CUDA/Blackwell runtime.
5. [`MODELS.md`](MODELS.md) — pinned model ids/revisions.
6. [`VALIDATION_LAB.md`](VALIDATION_LAB.md) — Validation, history drift и build comparison.
7. [`RUNTIME_DATA.md`](RUNTIME_DATA.md) — SQLite, logs, caches и results.
8. [`SAFE_STOP.md`](SAFE_STOP.md) — Safe Stop semantics.
9. [`VALIDATION_BASELINE.md`](VALIDATION_BASELINE.md) — исторические regression baselines; не описание активного runtime.
10. [`../ROADMAP.md`](../ROADMAP.md) — единственный актуальный roadmap.

## Правило актуальности

Активная продуктовая документация описывает v0.4.x. Упоминания старых версий допустимы только в явно историческом regression/baseline контексте. Старые portable/runtime инструкции не являются частью текущей документации.
