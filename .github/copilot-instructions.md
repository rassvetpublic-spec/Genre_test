# Genre_test Copilot repository instructions

Read and obey the repository-root `AGENTS.md` before planning or changing files.

Genre_test is the canonical engineering repository for the AUDIO_MASTERING project. Stable v0.4 analysis and active v0.5 retrieval are protected baselines while repair, technical-QC, mastering, A/B/X, metadata, and delivery capabilities are added incrementally.

Use GitHub Issues as the task contract. Keep work bounded to the Issue acceptance criteria. Prefer a focused branch and PR. Never commit directly to `main`.

Never merge, enable auto-merge, or treat a PR as authorized to merge unless explicit user MTD authority covers it. `mtd`, `MTD`, or `мтд` may authorize the current ready PR or a sequential merge train across multiple planned PRs inside one already agreed project plan. Sequential authority never extends to unrelated PRs or silent scope expansion, and every PR must independently pass READY-MTD/current-head validation before merge.

For Ozone/mastering work, preserve the architecture in `docs/mastering/ozone12/` and related config/tools. Ozone module order is semantically significant. REAPER is the render host. Ozone/REAPER must remain optional and must not become dependencies of ordinary analysis/retrieval startup.

Backend-neutral audio measurements belong in shared technical/QC code. Ozone-specific XML, ParamID/schema/build guards, ElementChain/module-order, preset and render logic belong in the Ozone mastering boundary. Do not duplicate shared mastering meters inside backend-specific code.

Source audio is immutable. Derived audio must be traceable. Do not commit private corpora, user tracks, session renders, model weights, runtime databases, caches, or secrets.

Before declaring READY-MTD: run relevant tests and repository CI, check scope and backward compatibility, update docs/contracts when required, and surface unresolved real-Windows/audio validation explicitly. During a sequential MTD train, stop on failed CI, conflicts, unexpected scope, missing evidence, or a new decision point.
