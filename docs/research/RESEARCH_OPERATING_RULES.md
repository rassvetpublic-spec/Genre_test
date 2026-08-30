# Genre_test Research Operating Rules

Status: **canonical operating contract for external research coverage**

This document defines the minimum rules that keep Genre_test research reproducible and self-contained in the repository. Chat history is not a source of truth.

## 1. Repository is the source of truth

Research decisions, discovered tools, test obligations, blockers and reproducible findings that affect the project must be recorded in GitHub. A future researcher must be able to continue the work without access to the chat that produced it.

Primary machine-readable ledger:

`docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json`

Human-readable audio R&D reference:

`docs/OPEN_SOURCE_AUDIO_RND_REFERENCES.md`

When Research Radar has a more specific canonical instruction for a run, the current files from `main` must be read before execution; remembered chat instructions do not override repository state.

## 2. No discovered candidate may silently disappear

Every relevant newly discovered detector, provenance/watermark system, forensic analyzer, model family, adversarial/robustness implementation, benchmark source, restoration transform or artifact-cleanup source must enter the registry.

Each entry must have an explicit lifecycle state. It must either be tested, remain queued, carry a concrete blocker, be marked for retest, or be explicitly rejected/superseded with a reason.

Similar models bundled in one repository do not automatically count as one test unit when their behavior can provide independent evidence.

## 3. Test-or-block rule

`test_required: true` is an obligation, not a recommendation.

A required candidate must progress toward a reproducible test unless an explicit blocker prevents it. Blockers must identify the reason, for example access, dependency, dataset, compute, authorization, disclosure or service terms.

External upload services may only receive fixtures that are appropriate and authorized for third-party disclosure. If that gate cannot be satisfied, preserve the candidate and record the blocker instead of dropping it.

## 4. Controlled robustness loop

Detector/provenance bypass methods are used only as controlled adversarial research instruments for robustness and defense adaptation.

Canonical loop:

`baseline -> controlled challenge/transform -> characterize failure -> defensive adaptation/calibration -> clean + challenged retest`

A successful controlled bypass is a robustness finding. It must produce a defensive follow-up or an explicit conclusion explaining why no defensive change is justified.

Production mastering/cleanup must not be optimized for real-world detector evasion or provenance circumvention.

## 5. Evidence contract

Test results must preserve enough information to reproduce and interpret the result. The registry defines mandatory result fields. At minimum preserve fixture identity/hash, tool/model revision, test mode, baseline and challenged results, perceptual/content impact, defensive follow-up and evidence location.

Measurements, interpretation and subjective listening observations must remain distinguishable.

Vendor scores and upstream claims are evidence inputs, not project ground truth, until independently reproduced where reproduction is possible.

## 6. Audio transformation QC

Cleanup, restoration, mastering and resynthesis experiments must protect against improvement-by-score-only.

Use appropriate controls including loudness-matched A/B, original/bypass as a valid winner, delta/Removed audition where applicable, transient/content-retention checks and codec/delivery robustness tests.

Do not promote universal HF cuts, unconditional air restoration, resynthesis or aggressive cleanup without fixture-specific evidence.

## 7. Upstream source watch

Registered sources with `watch_required: true` must be checked periodically. The default cadence is weekly unless a source justifies another cadence.

Watch for material releases/commits, model or checkpoint changes, detector methods, watermark/provenance changes, adversarial/defense methods, benchmark/evaluation changes, API/access changes and material README/architecture updates.

Record `last_checked` and the upstream revision when known. Never invent a revision; use an explicit unknown/null state when it cannot be established.

If an upstream change can alter measured behavior, compatibility, access or benchmark semantics, move the affected entry to `RETEST_REQUIRED` and retest before promoting claims based on the new version.

## 8. Coverage reconciliation

Before claiming broad detector/robustness coverage, a research run must reconcile its scope against `AI_AUDIO_TOOL_TEST_REGISTRY.json`.

A summary must not imply that all tools were tested when some remain discovered, blocked or awaiting retest. Missing evidence is reported as missing evidence.

## 9. Change discipline

New research knowledge should update the smallest appropriate canonical artifact rather than accumulating only in PR discussion or chat.

Machine-actionable state belongs in the JSON registry. Detailed verified technical context belongs in the relevant research document. Reproducible run evidence belongs in the project's designated evidence/run location.

Historical failed CI runs, obsolete intermediate SHAs and conversational reasoning are not canonical research knowledge unless they expose a persistent engineering constraint that future work must know.

## 10. Definition of repository-complete research

A research topic is considered transferred from chat into Genre_test when all project-relevant durable knowledge is represented by one or more of:

- a canonical document;
- a machine-readable registry/state entry;
- reproducible test evidence;
- executable code/test/workflow;
- an explicit blocker or follow-up obligation.

If deleting the originating chat would cause a future researcher to lose a project-relevant decision, test obligation, verified source, blocker or reproducible finding, the transfer is incomplete.
