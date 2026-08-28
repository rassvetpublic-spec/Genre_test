# Genre_test Agent Constitution

This repository is the canonical engineering source of truth for the AUDIO_MASTERING project.

## Authority and merge policy

- Never commit directly to `main`.
- Normal change flow: Issue -> branch -> PR -> CI -> review -> READY-MTD.
- No agent may merge a pull request unless the user explicitly issues `mtd`, `MTD`, or `мтд`, either for the current ready PR or for a previously agreed sequential MTD plan that includes it.
- An explicit MTD may authorize a sequential merge train across multiple planned PRs within one project when the user has already approved that plan. It does not authorize unrelated PRs, unplanned scope expansion, or work outside that project plan.
- Every PR in an authorized merge train must independently reach READY-MTD and be revalidated against its current head SHA before merge.
- Stop the merge train and return to the user if CI fails, mergeability changes, an unexpected scope change appears, required evidence is missing, or a new product/architecture decision is needed.
- After every authorized merge: verify post-merge CI/test state and confirm the head branch is deleted. If automatic deletion did not occur, report the leftover branch for repository stewardship.
- Do not enable auto-merge as a substitute for explicit MTD authority.

## Product boundary

`Genre_test` is evolving into the local-first AUDIO_MASTERING studio-finish system. Stable v0.4 analysis and active v0.5 retrieval must remain independently usable while later repair/mastering subsystems are developed.

Ozone 12 Advanced is an optional mastering backend inside Genre_test, not a separate product. REAPER is the render host for Ozone work.

The historical `rassvetpublic-spec/OZONE12_MASTERING_LAB` repository is migration/provenance evidence until consolidation is complete; new engineering belongs here.

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

## Role separation

Use the repository custom agents for specialized work:

- `repo-steward`: repository hygiene and state consistency.
- `researcher`: evidence gathering and proposal Issues; does not implement product code.
- `architect`: architecture review, boundary decisions, decomposition and acceptance criteria.
- `coder`: implementation from approved, bounded work; stops at PR.
- `qa-reviewer`: code/test/CI/regression review and change requests.
- `audio-science`: DSP/audio/mastering validity review and measurement semantics.
- `release-manager`: final readiness gate; merges only under explicit current MTD authority, including an active approved sequential MTD plan.

The implementation agent must not be the sole reviewer of its own work.

## Scope discipline

- Prefer one focused Issue -> one focused PR when practical.
- Do not silently expand v0.5 CLaMP work into v0.6/v0.7 implementation.
- Research findings become proposals before implementation unless the user explicitly requests immediate code and the change is already within an approved Issue.
- Preserve backward compatibility with stable analysis/retrieval unless a dedicated migration explicitly changes it.
- New optional backends must fail independently rather than breaking ordinary analysis startup.

## Required checks

Before declaring a PR READY-MTD:

1. Re-read the Issue and acceptance criteria.
2. Review the diff for accidental scope growth and generated/private artifacts.
3. Run the relevant focused tests plus repository CI gates.
4. Confirm documentation/contracts were updated when behavior or schema changed.
5. For audio/DSP/Ozone changes, obtain Audio Science review in addition to ordinary QA.
6. Report unresolved risks, unknowns, and any required real-Windows/audio validation explicitly.

## Repository hygiene

- Do not commit local audio, private corpora, model weights, caches, `.venv`, runtime databases, or session renders unless a fixture is intentionally reviewed for Git inclusion.
- Do not delete an unmerged branch merely because it looks stale.
- A branch with an open PR, unique commits, or unclear ownership is not disposable.
- Merged branches may be deleted after post-merge verification; GitHub automatic head-branch deletion is preferred.
- Keep roadmap/current/TODO documents aligned with actual merged state, not merely open PR state.
