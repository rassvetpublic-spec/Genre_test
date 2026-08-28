---
applyTo: ".github/**,AGENTS.md,docs/AGENT_WORKFLOW.md"
---

Repository workflow changes must preserve the explicit Issue -> branch -> PR -> CI/review -> READY-MTD -> explicit user MTD authority -> merge -> post-merge CI -> branch deletion state machine.

Do not weaken or bypass these rules:

- never commit directly to `main`;
- never enable auto-merge as a substitute for user authorization;
- `mtd`, `MTD`, or `мтд` may authorize one current ready PR or a sequential merge train across multiple planned PRs in one already agreed project plan;
- sequential MTD authority never covers unrelated work or silent scope expansion;
- every PR in the train must independently pass READY-MTD/current-head validation before merge;
- if the PR head SHA changes after readiness, revalidate before merging;
- after every merge, verify CI/test state on `main` and confirm the merged head branch is deleted before continuing;
- stop a sequential merge train on CI failure, conflict, unexpected scope, missing evidence, or a new product/architecture/release decision;
- do not delete unmerged branches with unique commits, open PRs, or unclear ownership.

Custom agents must use least-privilege intent and explicit stop conditions. `RESEARCHER` must not silently implement product code. `CODER` stops at PR. `QA_REVIEWER` and `AUDIO_SCIENCE` may block readiness. `RELEASE_MANAGER` may declare `READY-MTD` but must verify that current explicit MTD authority actually covers the PR before merging.

Changes to CI, agent definitions, repository instructions, or release/merge policy should include deterministic validation where practical and must not disable existing analysis/retrieval gates merely to make CI green.
