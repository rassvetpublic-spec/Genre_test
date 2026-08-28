# Agent workflow for Genre_test

This document explains how repository-aware agents should collaborate without weakening the project's explicit merge authority.

## State machine

```text
IDEA / REQUEST
    |
    v
ISSUE CONTRACT
    |
    v
BRANCH
    |
    v
IMPLEMENTATION
    |
    v
PULL REQUEST
    |
    +--> QA_REVIEWER -----------+
    |                           |
    +--> AUDIO_SCIENCE* --------+--> CHANGES / RE-TEST
    |                           |
    +--> CI --------------------+
                                |
                                v
                           READY-MTD
                                |
                explicit user MTD authority
                  for this PR or plan
                                |
                                v
                              MERGE
                                |
                                v
                      POST-MERGE CI / TEST
                                |
                                v
                       DELETE HEAD BRANCH
                                |
                   planned next PR exists?
                       /              \
                     yes              no
                      |                |
             revalidate READY-MTD     DONE
                      |
          continue only while the same
          approved MTD plan is valid
```

`AUDIO_SCIENCE` is required for DSP, audio-analysis, restoration, stereo, transient, codec, loudness, mastering, Ozone XML/preset/module-order, and render-path changes.

## Role handoffs

### REPO_STEWARD

Use for repository state, stale branches, duplicated implementations, roadmap/current-file consistency, ignored artifacts, and source-of-truth questions. It may identify safe cleanup but must not delete an unmerged branch with unique or unclear work.

### RESEARCHER

Use for external evidence, libraries, DSP methods, model/tool surveys, or implementation alternatives. Research should normally end in a proposal or Issue update. It must not silently turn research into product-code implementation.

### ARCHITECT

Use before broad or boundary-changing work. It defines ownership, dependency direction, contracts, migration strategy, acceptance criteria, and decomposition into bounded Issues/PRs.

### CODER

Use after scope is approved. It implements the bounded change, adds/updates tests and docs, and stops at a PR. It does not merge and should not be the sole reviewer of its own work.

### QA_REVIEWER

Use on the PR diff and current head SHA. It reviews correctness, regressions, tests, failure modes, compatibility, accidental scope growth, and repository hygiene. It may block readiness.

### AUDIO_SCIENCE

Use independently for audio/DSP/mastering correctness. It distinguishes measured evidence from engineering interpretation and subjective preference. It may block readiness even when ordinary CI is green.

### RELEASE_MANAGER

Use only after implementation/review. It checks the Issue contract, reviews, CI, mergeability, documentation, external validation requirements, unresolved risks, and whether explicit MTD authority covers the current PR. It returns `READY-MTD`, `NOT-READY`, or `INCONCLUSIVE`. `READY-MTD` alone is not merge authorization.

## MTD semantics

The accepted explicit merge tokens are:

```text
mtd
MTD
мтд
```

An explicit MTD can authorize either:

1. one specific READY-MTD PR; or
2. a sequential merge train across multiple planned PRs inside one already agreed project plan.

For a sequential merge train, the MTD remains valid only while the work stays inside that approved plan. It never authorizes unrelated PRs or silent scope expansion.

Each PR in the train still requires its own readiness gate:

1. Re-read the current PR and current head SHA.
2. Confirm the PR is part of the approved MTD plan.
3. Confirm required CI/reviews still apply to that head.
4. Confirm the PR is mergeable and scope has not changed unexpectedly.
5. Merge the PR.
6. Verify the post-merge CI/test run on `main`.
7. Confirm the merged head branch is deleted; GitHub automatic deletion is preferred.
8. Only then proceed to the next planned READY-MTD PR.

Stop the sequential MTD train and return to the user if any of the following occurs:

- CI or required validation fails;
- the PR becomes non-mergeable or conflicts appear;
- the current head introduces unexpected scope;
- required evidence is missing or inconclusive;
- a new product, architecture, safety, or release decision is needed;
- the next PR is not part of the already agreed project plan.

Auto-merge must not be enabled as a substitute for explicit MTD authority. If a head SHA changes before merge, revalidate it. If post-merge CI fails, do not continue the train until the failure is triaged.

## Protected baselines

- Stable v0.4 analysis must remain usable.
- Active v0.5 retrieval must remain independently usable.
- Optional restoration/mastering backends must fail independently rather than break normal startup.
- Source audio is immutable.
- `Genre_test` is the canonical engineering source of truth for AUDIO_MASTERING.

## Ozone-specific handoff

Ozone 12 Advanced is an optional mastering backend with REAPER as render host. Ozone module order is part of preset semantics, not cosmetic metadata. A change to module order requires explicit review of phase, transient/sustain behavior, dynamics, harshness, stereo consequences, downstream Dynamic EQ/de-essing, and Maximizer/True Peak interaction.

Backend-neutral metrics belong in shared technical/QC layers. Ozone XML, ParamID/schema/build guards, ElementChain/module order, preset construction, and REAPER/Ozone render orchestration stay inside the mastering/Ozone boundary.
