# Agent workflow for Genre_test

This document defines how repository-aware agents collaborate without weakening user architecture authority, exact-head validation, or the project's standing automatic MTD authorization.

Read `AGENTS.md` first. GitHub Issues are task contracts; repository/GitHub state, not chat memory, carries durable workflow context.

## State machine

```text
REQUEST
  |
  v
SCOPED
  |
  +--> architecture/material contract decision required?
  |        |
  |       yes
  |        v
  |   ARCHITECTURE-READY
  |        |
  +--------+
  |
  v
CLAIMED
  |
  v
IMPLEMENTING
  |
  v
PULL REQUEST
  |
  v
REVIEW
  |
  +--> QA_REVIEWER ------------------+
  |                                  |
  +--> AUDIO_SCIENCE* ---------------+--> CHANGES / RE-TEST
  |                                  |
  +--> CI ---------------------------+
                                     |
                                     v
                                VALIDATION
                                     |
                                     v
                           READY-MTD <head-sha>
                                     |
                    standing project MTD authority
                    or explicit user MTD override
                                     |
                                     v
                                  MERGED
                                     |
                                     v
                         POST-MERGE-VERIFIED
                                     |
                                     v
                                  CLOSED
```

Stop/escalation states:

```text
BLOCKED
NEEDS-EVIDENCE
AMENDMENT-REQUIRED
NEEDS-USER-APPROVAL
```

They do not count as successful forward progress.

`AUDIO_SCIENCE` is mandatory for DSP/audio-analysis/restoration/repair/stems, stereo/mono, transient, codec, loudness, mastering, A/B/X audio methodology, Ozone XML/ParamID/preset/module-order, and REAPER/Ozone render/readback changes.

## Lifecycle ownership

| Transition | Primary owner | Gate |
|---|---|---|
| REQUEST creation | USER or RESEARCHER | concrete problem/proposal |
| REQUEST -> SCOPED | REPO_STEWARD; ARCHITECT when architecture is material | no duplicate/ambiguous scope |
| SCOPED -> ARCHITECTURE-READY | ARCHITECT | implementation-ready architecture inside approved authority |
| SCOPED/ARCHITECTURE-READY -> CLAIMED | REPO_STEWARD | no competing implementation claim/branch/PR |
| CLAIMED -> IMPLEMENTING | CODER | branch from current approved base |
| IMPLEMENTING -> PULL REQUEST | CODER | bounded implementation + evidence |
| PULL REQUEST -> REVIEW | CODER | current head published for independent review |
| REVIEW -> VALIDATION | QA_REVIEWER; AUDIO_SCIENCE when triggered | exact-head verdicts available |
| VALIDATION -> READY-MTD | RELEASE_MANAGER | all required exact-head gates satisfied |
| READY-MTD -> MERGED | RELEASE_MANAGER under standing/explicit user MTD | immediate current-head revalidation |
| MERGED -> POST-MERGE-VERIFIED | RELEASE_MANAGER | main CI/test state verified |
| POST-MERGE-VERIFIED -> CLOSED | REPO_STEWARD verifies repository/task state | Issue complete, branch state confirmed |

No role may skip a transition merely because it has broader GitHub credentials.

## Claim and duplicate-work rule

Before `CODER` starts production work, `REPO_STEWARD` checks the current Issue, open Issues, active branches, and open PRs for overlapping implementation scope.

The intended invariant is:

```text
one implementation Issue
-> at most one active implementation claim
-> at most one active implementation branch
-> at most one active implementation PR
```

Until PR-2 implements the GitHub-native claim fields/templates, record the collision check in the task/PR handoff and stop on ambiguous ownership.

## Role handoffs

### REPO_STEWARD

Use for repository/task state, overlapping work, stale branches, duplicated implementations, roadmap/current-file consistency, ignored artifacts, and source-of-truth questions.

It may certify `STATE-CLEAR` / `CLAIM-APPROVED` or block work with `STATE-CONFLICT` / `CLAIM-BLOCKED`. It does not implement product code, approve architecture, declare READY-MTD, merge, or delete branches. Leftover merged branches are reported to `RELEASE_MANAGER`.

### RESEARCHER

Use for external evidence, libraries, DSP methods, model/tool surveys, or implementation alternatives.

Research normally ends in a repository-backed proposal/handoff for `ARCHITECT`. It must not silently turn research into product-code implementation or update roadmap priority by itself.

### ARCHITECT

Use before broad, boundary-changing, persistent-contract, or schema work.

It defines ownership, dependency direction, contracts, migration strategy, acceptance criteria, required reviewers/evidence, allowed/forbidden paths, and bounded Issues/PRs.

Within an already approved architecture it may return `ARCHITECTURE-READY`. A new/material architecture, product, safety, or release decision requires explicit user approval; return `AMENDMENT-REQUIRED` or `NEEDS-USER-APPROVAL` rather than choosing silently.

### CODER

Use after scope is approved and claimed.

It implements the bounded change, adds/updates tests and docs, and stops at a PR. It does not change approved scope, declare READY-MTD, merge, or become the sole reviewer of its own work.

If the implementation requires crossing allowed paths, changing a contract beyond the approved design, or making a new architecture decision, stop with `AMENDMENT-REQUIRED`.

### QA_REVIEWER

Use on the PR diff and exact current head SHA.

It reviews software correctness, regressions, tests, failure modes, compatibility, accidental scope growth, and repository hygiene. Its verdict is exact-head scoped:

```text
QA_APPROVED <40-char-sha>
QA_CHANGES_REQUESTED <40-char-sha>
QA_BLOCKED <40-char-sha>
```

It may block validation. It does not declare READY-MTD or merge.

### AUDIO_SCIENCE

Use independently when the audio trigger applies.

It validates DSP/audio/mastering/Ozone semantics and methodology, separating measured evidence, engineering interpretation, and listening preference. Its verdict is exact-head scoped:

```text
AUDIO_APPROVED <40-char-sha>
AUDIO_CHANGES_REQUESTED <40-char-sha>
AUDIO_INCONCLUSIVE <40-char-sha>
```

It may block validation even when ordinary CI/QA is green. It does not implement product code, declare READY-MTD, or merge.

### RELEASE_MANAGER

Use only after independent implementation/review evidence exists.

It aggregates the Issue contract, QA verdict, Audio Science verdict when required, exact-head CI, mergeability, documentation/evidence requirements, external validation state, and unresolved blockers.

It returns:

```text
READY-MTD <40-char-sha>
NOT-READY
INCONCLUSIVE
```

`RELEASE_MANAGER` is not a second full QA reviewer and must not replace missing independent verdicts with its own judgement.

Only `RELEASE_MANAGER` may declare READY-MTD, execute merge, and delete the successfully merged head branch. In this project, standing automatic MTD authorizes that execution once an approved-scope PR reaches exact-head READY-MTD; no fresh token is required unless the user narrows/pauses/revokes that standing authority.

## Standard handoff core

Until PR-2 implements formal GitHub templates, preserve these fields in every material handoff:

```text
issue
from_role
to_role
repository
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

If the receiver cannot reconstruct these fields from repository/GitHub state, the handoff is incomplete.

## Exact-head readiness

READY-MTD is not a floating property of a PR. It must always bind to the exact current head SHA:

```text
READY-MTD <40-char-sha>
```

If the head SHA changes after QA, Audio Science, validation, or readiness, previous exact-head verdicts are stale and the PR returns to the required validation gates.

## MTD semantics

### Standing automatic MTD

The user has granted standing automatic MTD authorization for the Genre_test project. It covers merge execution for PRs that:

1. belong to an already approved task or sequential implementation plan;
2. independently reach `READY-MTD <current-head-sha>`;
3. pass immediate current-head revalidation;
4. do not introduce new/material architecture, scope expansion, unrelated work, or unresolved decision points.

A fresh `mtd` token is therefore not required for each ready PR while this standing authorization remains active.

The accepted explicit merge tokens remain:

```text
mtd
MTD
мтд
```

They may be used by the user to authorize/narrow a one-off merge or train, but do not weaken the exact-head gates.

For every automatic or explicitly authorized sequential merge train:

1. Re-read the current PR and current head SHA.
2. Confirm the PR is part of the approved plan/scope.
3. Confirm required QA and Audio Science verdicts, CI and evidence apply to this exact head.
4. Confirm the PR is mergeable and scope has not changed unexpectedly.
5. Merge the PR.
6. Verify the post-merge CI/test run on `main`.
7. Confirm/delete the merged head branch; only `RELEASE_MANAGER` may perform explicit deletion.
8. Only then proceed to the next planned `READY-MTD <sha>` PR.

Stop the train and return to the user if any of the following occurs:

- CI or required validation fails;
- the PR becomes non-mergeable or conflicts appear;
- the current head introduces unexpected scope;
- required evidence is missing or inconclusive;
- a new product, architecture, safety, or release decision is needed;
- an approved contract must be amended;
- the next PR is not part of the already agreed project plan.

GitHub auto-merge must not be enabled as a substitute for these gates. If post-merge CI fails, do not continue the train until the failure is triaged.

## Protected baselines

- Existing analysis must remain usable unless an approved migration changes it.
- Active v0.5 retrieval must remain independently usable.
- Optional restoration/mastering backends must fail independently rather than break normal startup.
- Source audio is immutable.
- `Genre_test` is the canonical engineering source of truth for AUDIO_MASTERING.
- Legacy Ozone material is reference/provenance evidence, not a higher-priority active architecture source.

## Ozone-specific handoff

Ozone 12 Advanced is an optional mastering backend with REAPER as render host. Ozone module order is part of preset semantics, not cosmetic metadata. A change to module order requires explicit review of phase, transient/sustain behavior, dynamics, harshness, stereo consequences, downstream Dynamic EQ/de-essing, and Maximizer/True Peak interaction.

Backend-neutral metrics belong in shared technical/QC layers. Ozone XML, ParamID/schema/build guards, ElementChain/module order, preset construction, and REAPER/Ozone render orchestration stay inside the mastering/Ozone boundary.
