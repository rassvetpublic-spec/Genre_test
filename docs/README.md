# Genre_test documentation

Актуальная документация описывает текущую линию **0.5.0.dev0**, при этом стабильное поведение ядра анализа v0.4 сохраняется как regression baseline.

1. [`../README.md`](../README.md) — основной README и быстрый вход.
2. [`ACTIVE_CURRENT.md`](ACTIVE_CURRENT.md) — фактическое текущее состояние продукта.
3. [`KNOWLEDGE_BASE.md`](KNOWLEDGE_BASE.md) — проверенные инженерные наблюдения, причины ключевых инвариантов и исторические failure modes, которые важно не потерять.
4. [`ARCHITECTURE.md`](ARCHITECTURE.md) — MAEST + AudioSet AST + DSP + AudioProfile.
5. [`GPU_RUNTIME.md`](GPU_RUNTIME.md) — Python / PyTorch / CUDA / Blackwell runtime.
6. [`MODELS.md`](MODELS.md) — pinned model ids и revisions.
7. [`CLAMP3_ROADMAP.md`](CLAMP3_ROADMAP.md) и [`CLAMP3_ARCHITECTURE.md`](CLAMP3_ARCHITECTURE.md) — активная retrieval-линия v0.5.
8. [`VALIDATION_LAB.md`](VALIDATION_LAB.md) — Validation, history drift и build comparison.
9. [`RUNTIME_DATA.md`](RUNTIME_DATA.md) — SQLite, logs, caches и results.
10. [`SAFE_STOP.md`](SAFE_STOP.md) — Safe Stop semantics.
11. [`../ROADMAP.md`](../ROADMAP.md) — единственный актуальный продуктовый roadmap.

## Правило актуальности

`ACTIVE_CURRENT.md` и `ROADMAP.md` определяют текущий статус и планы. `KNOWLEDGE_BASE.md` хранит durable engineering knowledge: реальные smoke/regression наблюдения, границы интерпретации моделей и уже исправленные классы ошибок, которые могут повториться.

Старые portable/runtime инструкции 0.3.x не являются активной документацией. Исторические уроки из них допускаются только в knowledge base как объяснение текущих инвариантов и требований к будущей упаковке.
