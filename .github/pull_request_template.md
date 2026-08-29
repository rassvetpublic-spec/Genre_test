<!--
Genre_test Agent System v2 implementation handoff.
Keep this PR linked to exactly one implementation Issue unless the approved task explicitly says otherwise.
GitHub Issue + this PR are the durable work record; do not create a parallel WORK_MANIFEST.
Any PR-head change invalidates earlier exact-head QA / AUDIO / READY-MTD verdicts.
Use a non-closing Issue reference here: the Issue is closed only after MERGED -> POST-MERGE-VERIFIED.
-->

Refs #

## Workflow contract

- Issue: #
- From role: `CODER`
- To role: `QA_REVIEWER`
- Workflow state: `REVIEW`
- Base SHA: `<40-char-sha>`
- PR head SHA: `<40-char-sha>`
- Implementation branch: `<branch>`
- Roadmap phase: `<phase>`

## Scope

<!-- Copy the bounded Issue scope; do not broaden it here. -->

## Allowed paths

- 

## Forbidden paths

- 

## Dependencies

- 

## Claim / collision check

- [ ] The linked Issue was `CLAIMED` before production implementation.
- [ ] Active Issues were checked for overlapping implementation scope.
- [ ] Active branches were checked for competing implementation ownership.
- [ ] Open PRs were checked for competing implementation ownership.
- [ ] This Issue has at most one active implementation branch and one active implementation PR.

Collision result / evidence:

## Acceptance criteria mapping

| Issue acceptance criterion | Implementation / evidence |
|---|---|
|  |  |

## Tests and CI

- Focused tests:
- Full/local checks:
- CI run/status:

## Required reviews

- [ ] `QA_REVIEWER` exact-head verdict required.
- [ ] `AUDIO_SCIENCE` required — or mark SKIP below with a reason that the audio trigger does not apply.

AUDIO_SCIENCE status / skip reason:

## Produced evidence

- 

## Open risks

- None / 

## Unresolved decisions

- None / 

## Scope audit

- [ ] Changed files stay inside approved paths.
- [ ] No forbidden/generated/private artifacts are included.
- [ ] No new/material architecture or product decision was introduced silently.
- [ ] No unrelated roadmap work was added.

## Next allowed action

`QA_REVIEWER exact-head review`

## MTD / release note

Standing automatic MTD may be used only after `READY-MTD <current-head-sha>` for approved scope, immediate current-head revalidation, required exact-head QA/Audio verdicts, green CI, mergeability, and no unresolved blocker or new decision point. `RELEASE_MANAGER` is the only role allowed to execute merge and explicit merged-head deletion.

Do not use `Closes`, `Fixes`, or `Resolves` for the implementation Issue. Keep the Issue open through merge and post-merge verification; close it only after the `POST-MERGE-VERIFIED` gate succeeds.
