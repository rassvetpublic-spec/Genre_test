# Genre_test Agent Constitution

This repository is the canonical engineering source of truth for the AUDIO_MASTERING project.

## Authority and decision policy

The user is the final authority for:
- new or materially changed architecture;
- scope expansion outside an already approved task/plan;
- roadmap priority changes;
- breaking contract/schema decisions that were not already approved;
- merge authorization through explicit `mtd`, `MTD`, or `мтд`.

`ARCHITECT` may certify architecture, ownership, decomposition, contracts, and acceptance criteria inside already approved constraints. If implementation requires a new/material architecture, product, safety, or release decision, the workflow must stop with `AMENDMENT-REQUIRED` or `NEEDS-USER-APPROVAL`; an agent must not infer approval from silence.

## Merge policy

- Never commit directly to `main`.
- Normal change flow: REQUEST -> SCOPED -> optional ARCHITECTURE-READY -> CLAIMED -> IMPLEMENTING -> REVIEW -> VALIDATION -> READY-MTD -> explicit user MTD -> MERGED -> POST-MERGE-VERIFIED -> CLOSED.
- `BLOCKED`, `NEEDS-EVIDENCE`, and `AMENDMENT-REQUIRED` are stop/escalation states, not successful forward progress.
- No agent may merge a pull request unless the user explicitly issues `mtd`, `MTD`, or `мтд`, either for the current ready PR or for a previously agreed sequential MTD plan that includes it.
- An explicit MTD may authorize a sequential merge train across multiple planned PRs within one project when the user has already approved that plan. It does not authorize unrelated PRs, unplanned scope expansion, or work outside that project plan.
- Every PR in an authorized merge train must independently reach `READY-MTD <40-char-head-sha>` and be revalidated against that exact current head SHA before merge.
- Any head SHA change invalidates the prior READY-MTD verdict and returns the PR to validation.
- Stop the merge train and return to the user if CI fails, mergeability changes, an unexpected scope change appears, required evidence is missing, or a new product/architecture/safety/release decision is needed.
- After every authorized merge: verify post-merge CI/test state and confirm the head branch is deleted. If automatic deletion did not occur, `RELEASE_MANAGER` may delete that merged head branch only inside the current authorized MTD cycle; otherwise report it for repository stewardship.
- Do not enable auto-merge as a substitute for explicit MTD authority.

## Product boundary

`Genre_test` is evolving into the local-first AUDIO_MASTERING studio-finish system. Stable v0.4 analysis and active v0.5 retrieval must remain independently usable while later repair/mastering subsystems are developed.

Ozone 12 Advanced is an optional mastering backend inside Genre_test, not a separate product. REAPER is the render host for Ozone work.

The historical `rassvetpublic-spec/OZONE12_MASTERING_LAB` repository and `legacy/OZONE12_MASTERING_LAB/` content are reference/provenance evidence only. New engineering belongs in Genre_test and current `Genre_test/main` contracts take precedence over legacy material.

## Audio safety and truth rules

- Source audio is immutable. Never overwrite the source.
- Every repair/master render is a derived asset and should carry parent/source identity and processing provenance as contracts mature.
- Keep measured/file-metadata/model-inference/user-entered/derived information distinguishable.
- Do not claim a plug-in, processor, stem identity, section label, or subjective quality from rendered audio without evidence that supports that claim.
- A bypass/original candidate is a valid winner.
- Do not optimize for AI-origin detector evasion, watermark stripping, or provenance concealment.

## Ozone 12 mastering rules

Canonical direction: SUNO stereo source -> Ozone 12 Advanced -> WAV 24-bit / 48 kHz.

Module order is semantically significant. Do not treat an Ozone preset as an unordered bag of settings. Changes to chain order must be explicit, justified, and tested because order affects phase, dynamics, transient/sustain balance, stereo width, harshness, and loudness.

Safe default reasoning order:

```text
preparatory correction / balance
-> tonal EQ
-> gentle dynamics / transient processing
-> harshness control / stabilization
-> stereo processing
-> final Dynamic EQ / de-essing
-> Maximizer / True Peak limiter
```

Preserve Safe / Probe / Refine semantics. For transient/sustain processing, protect focused transient attack and avoid uncontrolled sustain widening. Lossy source handling must be explicit and conservative.

## Architecture ownership

Backend-neutral audio measurements belong in shared Genre_test technical/QC layers and must be reusable by repair, mastering, codec preview, and A/B/X review.

Ozone-specific XML, ParamID/schema/build guards, ElementChain/module-order logic, preset construction, and REAPER/Ozone render orchestration belong under the mastering/Ozone boundary.

Do not create a second active implementation of shared metrics inside an Ozone-specific tool.

## Role separation and authority

The specialized role set is intentionally limited to seven agents:

- `REPO_STEWARD`: repository/task-state consistency, duplicate-scope detection, claim/hygiene checks. It does not implement product code, approve architecture, declare READY-MTD, or merge.
- `RESEARCHER`: external evidence and bounded proposals. It does not implement product code or silently change roadmap/scope.
- `ARCHITECT`: architecture certification, subsystem ownership, contracts, decomposition, and acceptance criteria. New/material architecture decisions require explicit user approval.
- `CODER`: the production implementation role for approved bounded work. It stops at a reviewable PR and does not approve or merge its own work.
- `QA_REVIEWER`: independent software/code/test/regression verdict for the exact PR head SHA. It may block validation but does not declare READY-MTD.
- `AUDIO_SCIENCE`: independent DSP/audio/mastering/Ozone/methodology verdict for the exact PR head SHA when the audio trigger applies. It may block validation but does not declare READY-MTD.
- `RELEASE_MANAGER`: readiness aggregator and the only agent role allowed to execute merge/merged-head deletion, strictly inside explicit current MTD authority. It does not replace QA with a second full code review.

The implementation agent must not be the sole reviewer of its own work. No agent may expand its own authority by editing governance outside an approved governance task.

## Claim and duplication discipline

GitHub Issues are the task contracts. Before production implementation starts, the task must be `CLAIMED` after checking for overlapping active Issues, branches, and PRs.

Target invariant:

```text
one implementation Issue
-> at most one active implementation claim
-> at most one active implementation branch
-> at most one active implementation PR
```

Until the PR-2 claim mechanism is implemented, agents must perform this collision check explicitly before starting work and stop on ambiguity rather than create competing implementation.

## Audio/DSP review trigger

Independent `AUDIO_SCIENCE` review is mandatory for changes affecting:
- DSP or audio-analysis semantics;
- restoration/repair/stem processing;
- loudness, True Peak, transient, stereo/mono, codec, or measurement methodology;
- A/B/X audio comparison or level-matching methodology;
- mastering assumptions or candidate-selection semantics;
- Ozone XML parameter semantics, ParamID/schema/build guards, ElementChain/module order, preset/module policy;
- REAPER/Ozone render-path or readback compatibility.

Ordinary documentation/code changes outside those semantics do not require Audio Science merely because they live in an audio repository.

## Scope discipline

- Prefer one focused Issue -> one focused PR when practical.
- Do not silently expand v0.5 CLaMP work into v0.6/v0.7 implementation.
- Research findings become proposals before implementation unless the user explicitly requests immediate code and the change is already within an approved Issue.
- Preserve backward compatibility with stable analysis/retrieval unless a dedicated migration explicitly changes it.
- New optional backends must fail independently rather than breaking ordinary analysis startup.
- Approved/allowed paths and explicit non-goals are binding. If implementation must cross them, stop with `AMENDMENT-REQUIRED`.

## Required handoff core

Until PR-2 provides GitHub templates, every task handoff should preserve at minimum:

```text
issue
from_role
to_role
base_sha or pr_head_sha
workflow_state
scope
allowed_paths
forbidden_paths
dependencies
acceptance_criteria
required_evidence
produced_evidence
open_risks
unresolved_decisions
next_allowed_action
```

Do not use chat memory as the only carrier of these fields.

## Required checks

Before declaring `READY-MTD <sha>`:

1. Re-read the Issue/task contract and acceptance criteria.
2. Confirm the current PR head SHA and invalidate older verdicts if it changed.
3. Confirm QA approval applies to that exact SHA.
4. For audio-triggered work, confirm Audio Science approval applies to that exact SHA.
5. Review the diff for accidental scope growth and generated/private artifacts.
6. Confirm relevant focused tests plus repository CI gates are green for that exact SHA.
7. Confirm documentation/contracts/versioning were updated when behavior or schema changed.
8. Confirm mergeability against current `main`.
9. Report unresolved risks, unknowns, and required real-Windows/audio validation explicitly.
10. Confirm no `BLOCKED`, `NEEDS-EVIDENCE`, `AMENDMENT-REQUIRED`, or unresolved user decision remains.

`RELEASE_MANAGER` aggregates these gates; it must not silently substitute its own re-review for missing QA or Audio Science evidence.

## Repository-native context

A new repository-aware agent must recover state from repository/GitHub evidence rather than chat memory:

1. `AGENTS.md`;
2. `docs/ACTIVE_CURRENT.md`;
3. `ROADMAP.md` for phase context;
4. assigned GitHub Issue/task contract and current Issue/PR/branch state;
5. architecture/contracts relevant to affected paths;
6. nearby implementation/tests;
7. required review/evidence rules;
8. the single next permitted workflow transition.

If these sources disagree, stop, identify the conflict, and prefer current `Genre_test/main`/current GitHub state over legacy or historical chat context.

## Repository hygiene

- Do not commit local audio, private corpora, model weights, caches, `.venv`, runtime databases, or session renders unless a fixture is intentionally reviewed for Git inclusion.
- Do not delete an unmerged branch merely because it looks stale.
- A branch with an open PR, unique commits, or unclear ownership is not disposable.
- Merged branches may be deleted only after post-merge verification; GitHub automatic head-branch deletion is preferred.
- Keep roadmap/current/TODO documents aligned with actual merged state, not merely open PR state.
