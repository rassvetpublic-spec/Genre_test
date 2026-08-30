# Repository cold-start recovery contract

Purpose: a fresh repository-aware agent must be able to continue Genre_test engineering from `Genre_test/main` plus live GitHub state **without access to historical chat context**.

## Required recovery order

Read in this order before planning production work:

1. `AGENTS.md` — authority, governance, review triggers and merge policy.
2. `docs/ACTIVE_CURRENT.md` — current product version, milestone, protected baselines and active subsystem state.
3. `ROADMAP.md` — phase context and long-term dependencies.
4. Assigned/open GitHub Issue plus current PR/branch state — exact task contract, acceptance criteria, allowed/forbidden paths, collision/claim status and exact-head evidence.
5. `docs/ARCHITECTURE.md` and the affected subsystem architecture/contracts — ownership map and implementation boundaries.
6. Nearby implementation and tests.
7. Required review/evidence rules for the affected subsystem.
8. `docs/AGENT_WORKFLOW.md` — required handoff state and next permitted transition.

Legacy/frozen repositories or artifacts are evidence only unless a current Genre_test contract explicitly references them.

## Recovery checklist

Before implementation, the agent must be able to state all of the following from repository/GitHub evidence:

```text
PRODUCT
CURRENT VERSION
CURRENT MILESTONE
CURRENT ARCHITECTURE
PROTECTED BASELINES
COMPLETED WORK RELEVANT TO THE TASK
ACTIVE / BLOCKED WORK RELEVANT TO THE TASK
GOVERNANCE / ROLE AUTHORITY
ASSIGNED ISSUE / TASK CONTRACT
BASE OR PR HEAD SHA
ALLOWED PATHS
FORBIDDEN PATHS
DEPENDENCIES
REQUIRED EVIDENCE
UNRESOLVED DECISIONS
NEXT ALLOWED ACTION
```

If any material field cannot be recovered, the task is not cold-start safe and the agent must stop with `NEEDS-EVIDENCE`, `STATE-CONFLICT`, `AMENDMENT-REQUIRED`, or `NEEDS-USER-APPROVAL` as appropriate.

## Current architecture navigation

Use `docs/ARCHITECTURE.md` as the map, then switch to the authoritative subsystem documents:

| Area | Canonical entry points |
|---|---|
| Core analysis/history | `docs/ARCHITECTURE.md`, nearby `src/genre_test/**`, tests |
| CLaMP retrieval | `docs/CLAMP3_ARCHITECTURE.md`, `docs/CLAMP3_TODO.md`, `docs/CLAMP3_RUNTIME*.md` |
| Shared Technical QC | `docs/SUPERCOMBINE_TODO.md`, Issue #45, nearby shared QC code/tests |
| Repair / stems / vocals | `docs/GENERATIVE_DEFECT_PROFILE.md`, `docs/GENERATIVE_AUDIO_REPAIR_*.md`, Issues #50–#52/#63 |
| Ozone/REAPER mastering | `docs/mastering/ozone12/README.md`, integrated config/tools/code namespace |
| A/B/X review | Issue #54, `docs/SUPERCOMBINE_TODO.md` |
| Metadata / asset lineage | Issues #53/#56, `docs/SUPERCOMBINE_TODO.md` |
| Runtime / ComfyUI | Issues #46/#55, `docs/SUPERCOMBINE_TODO.md` |
| Agent workflow | `AGENTS.md`, `.github/copilot-instructions.md`, `docs/AGENT_WORKFLOW.md` |

## Live-state rule

Do not hard-code a single global "current issue" from a historical document. The live task is determined from the assigned Issue and current GitHub Issue/PR/branch state.

`docs/ACTIVE_CURRENT.md` may summarize known milestone state, but an Issue marked complete there must still be checked against live GitHub state before relying on it.

## Conflict policy

When sources disagree:

1. governance/authority: `AGENTS.md` wins;
2. task/workflow state: live GitHub Issue/PR/branch state wins;
3. current product/milestone summary: `docs/ACTIVE_CURRENT.md`;
4. architecture ownership: `docs/ARCHITECTURE.md` and the affected subsystem contract;
5. future plan: `ROADMAP.md` / TODO documents;
6. legacy material: historical/provenance evidence only.

Do not silently reconcile a material contradiction by guessing. Report the exact conflict and stop if it changes scope, architecture, release authority, evidence requirements, or the next workflow transition.

## Protected project facts

A cold-start agent must recover at least these invariants before changing relevant code:

- `Genre_test` is the canonical engineering repository for AUDIO_MASTERING.
- Existing MAEST + AudioSet AST + DSP analysis/history remains a protected baseline.
- v0.5 retrieval is an optional isolated CLaMP 3/MERT/XLM-R subsystem and must fail independently.
- Source audio is immutable; derived audio must be traceable.
- Ozone 12 Advanced is an optional mastering backend; REAPER is its render host.
- Backend-neutral technical measurements belong in shared QC, not duplicated inside Ozone-specific code.
- The historical `OZONE12_MASTERING_LAB` is frozen reference/provenance, not an active development destination.
- AI-origin detector evasion and provenance concealment are not project objectives.
- No direct commits to `main`.
- QA/Audio Science/READY-MTD evidence is exact-head scoped.
- Standing automatic MTD applies only to already approved-scope PRs that reach exact-head readiness; new/material decisions still require user approval.

## Task admission test

A task may enter implementation only if all statements below are true:

```text
[ ] Issue/task contract exists and is current.
[ ] No competing active implementation claim/branch/PR owns the same scope.
[ ] Base SHA is known and current enough for the approved task.
[ ] Allowed and forbidden paths are known.
[ ] Architecture owner/boundary is known.
[ ] Required QA and Audio Science trigger are known.
[ ] Required local/CI/real-hardware evidence is known.
[ ] No unresolved user/material architecture decision is hidden in chat memory.
[ ] Exactly one next workflow transition is permitted.
```

If these conditions are not satisfied, implementation should not start.

## Cold-start acceptance test

The repository passes cold-start acceptance when a fresh agent, given only:

```text
Genre_test/main
+ live GitHub Issues / PRs / branches
```

and explicitly denied access to historical chats can correctly answer:

1. What is the product and current development version?
2. What milestone is active and what baselines are protected?
3. Which subsystem owns the requested change?
4. Which historical systems are frozen/reference-only?
5. What Issue owns the implementation and is it already claimed?
6. What files may and may not change?
7. What evidence/review gates apply?
8. What is the exact current branch/PR head when relevant?
9. Is a new user decision required?
10. What is the single next allowed workflow action?

A contradiction in those answers is a failed cold-start test, not permission to infer missing state from chat history.

## Automated consistency gate

`tools/check_repository_context.py` checks repository-local invariants that previously caused cold-start ambiguity, including:

- obsolete #27-as-current wording;
- retired v0.4 portable release paths in `ACTIVE_CURRENT`;
- explicit-MTD-only wording that conflicts with standing MTD governance;
- missing active development version / standing-MTD markers;
- stale `ARCHITECTURE — v0.4.0` framing;
- recovery-order drift from the sequence mandated by `AGENTS.md`;
- pre-#27 provisional-sidecar wording reappearing in `ROADMAP.md` or `docs/THIRD_PARTY_MODELS.md`;
- missing current subsystem navigation/cold-start markers.

CI runs the repository test suite, including `tests/test_repository_context.py`; the checker can also be run directly:

```powershell
python .\tools\check_repository_context.py
```

The automated gate is intentionally repository-local and network-free. Live Issue/PR state still requires GitHub inspection at task start.
