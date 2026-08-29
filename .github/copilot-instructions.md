# Genre_test Copilot repository instructions

Read and obey the repository-root `AGENTS.md` before planning or changing files.

Genre_test is the canonical engineering repository for the AUDIO_MASTERING project. Existing analysis and active v0.5 retrieval are protected operating baselines while repair, technical-QC, mastering, A/B/X, metadata, and delivery capabilities are added incrementally.

Use GitHub Issues as task contracts. Recover durable state from current repository/GitHub evidence rather than chat memory. Keep work bounded to the Issue acceptance criteria, allowed paths, forbidden paths, dependencies, and non-goals.

Before production implementation, confirm the task is unambiguously claimable and no overlapping active Issue/branch/PR already owns the same implementation scope. The v2 lifecycle is:

```text
REQUEST -> SCOPED -> optional ARCHITECTURE-READY -> CLAIMED -> IMPLEMENTING
-> REVIEW -> VALIDATION -> READY-MTD <head-sha> -> MTD-authorized merge
-> MERGED -> POST-MERGE-VERIFIED -> CLOSED
```

`BLOCKED`, `NEEDS-EVIDENCE`, `AMENDMENT-REQUIRED`, and `NEEDS-USER-APPROVAL` are stop/escalation states.

New/material architecture, product, safety, breaking-contract, or release-policy decisions require explicit user approval. `ARCHITECT` may certify design inside already approved constraints but must not infer approval from silence.

Never commit directly to `main`. The user has granted standing automatic MTD for this project: once an approved-scope PR reaches exact-head READY-MTD, `RELEASE_MANAGER` may merge and perform post-merge cleanup without requesting a fresh token. Explicit `mtd`, `MTD`, or `мтд` remains a valid scoped override. Standing MTD does not authorize unrelated work, scope expansion, missing evidence, or new/material decisions.

READY-MTD is exact-head scoped. QA, Audio Science, CI, and readiness evidence must apply to the same current PR head SHA. Any head change invalidates old readiness evidence and requires revalidation.

Role authority:
- REPO_STEWARD: repository/task-state consistency and claim/hygiene checks; no production implementation/READY-MTD/merge/delete.
- RESEARCHER: evidence/proposals; no production implementation.
- ARCHITECT: architecture/contracts/decomposition inside approved authority; new/material decisions escalate to user.
- CODER: production implementation; stops at PR.
- QA_REVIEWER: exact-head software verdict; no READY-MTD/merge.
- AUDIO_SCIENCE: exact-head domain verdict for audio-triggered work; no READY-MTD/merge.
- RELEASE_MANAGER: readiness aggregation and the only role allowed to declare READY-MTD and execute merge/merged-head deletion under valid standing/explicit MTD.

Do not enable GitHub auto-merge as a substitute for governed exact-head release readiness.

For Ozone/mastering work, preserve the architecture in `docs/mastering/ozone12/` and related config/tools. Ozone module order is semantically significant. REAPER is the render host. Ozone/REAPER must remain optional and must not become dependencies of ordinary analysis/retrieval startup.

Backend-neutral audio measurements belong in shared technical/QC code. Ozone-specific XML, ParamID/schema/build guards, ElementChain/module-order, preset and render logic belong in the Ozone mastering boundary. Do not duplicate shared mastering meters inside backend-specific code.

Independent AUDIO_SCIENCE review is mandatory for DSP/audio-analysis/restoration/repair/stems, loudness/True Peak, transient, stereo/mono, codec, A/B/X audio methodology, mastering, Ozone semantic, or REAPER/Ozone render/readback changes.

Source audio is immutable. Derived audio must be traceable. Do not commit private corpora, user tracks, session renders, model weights, runtime databases, caches, or secrets.

Before declaring `READY-MTD <sha>`: confirm exact-head QA, Audio Science when required, relevant tests/CI, scope, backward compatibility, documentation/contracts, mergeability, and required external validation. Stop an automatic/sequential MTD train on failed CI, conflicts, unexpected scope, missing evidence, changed head without revalidation, or any new decision point.
