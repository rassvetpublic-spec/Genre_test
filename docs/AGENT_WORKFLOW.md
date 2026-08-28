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
                       fresh user MTD only
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
                                v
                              DONE
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

Use only after implementation/review. It checks the Issue contract, reviews, CI, mergeability, documentation, external validation requirements, and unresolved risks. It returns `READY-MTD`, `NOT-READY`, or `INCONCLUSIVE`. `READY-MTD` is not merge authorization.

## MTD semantics

The accepted explicit merge tokens are:

```text
mtd
MTD
мтд
```

One explicit token authorizes one merge cycle for the current ready PR only. It is consumed by that merge and cannot carry forward.

An authorized merge cycle is:

1. Re-read the current PR and current head SHA.
2. Confirm required CI/reviews still apply to that head.
3. Merge the PR.
4. Verify the post-merge CI/test run on `main`.
5. Confirm the merged head branch is deleted; GitHub automatic deletion is preferred.
6. Report merge SHA, post-merge result, branch state, and next unmerged task.

If the head changes before merge, revalidate. If post-merge CI fails, the merge is not considered operationally complete until the failure is triaged.

## Protected baselines

- Stable v0.4 analysis must remain usable.
- Active v0.5 retrieval must remain independently usable.
- Optional restoration/mastering backends must fail independently rather than break normal startup.
- Source audio is immutable.
- `Genre_test` is the canonical engineering source of truth for AUDIO_MASTERING.

## Ozone-specific handoff

Ozone 12 Advanced is an optional mastering backend with REAPER as render host. Ozone module order is part of preset semantics, not cosmetic metadata. A change to module order requires explicit review of phase, transient/sustain behavior, dynamics, harshness, stereo consequences, downstream Dynamic EQ/de-essing, and Maximizer/True Peak interaction.

Backend-neutral metrics belong in shared technical/QC layers. Ozone XML, ParamID/schema/build guards, ElementChain/module order, preset construction, and REAPER/Ozone render orchestration stay inside the mastering/Ozone boundary.
