---
applyTo: ".github/**,AGENTS.md,docs/AGENT_WORKFLOW.md"
---

Repository workflow changes must preserve the explicit Issue -> branch -> PR -> CI/review -> READY-MTD -> fresh user MTD -> merge -> post-merge CI -> branch deletion state machine.

Do not weaken or bypass these rules:

- never commit directly to `main`;
- never enable auto-merge as a substitute for user authorization;
- one explicit `mtd`, `MTD`, or `мтд` authorizes one merge cycle only;
- a prior MTD cannot be reused for another PR;
- if the PR head SHA changes after readiness, revalidate before merging;
- after merge, verify CI/test state on `main` and confirm the merged head branch is deleted;
- do not delete unmerged branches with unique commits, open PRs, or unclear ownership.

Custom agents must use least-privilege intent and explicit stop conditions. `RESEARCHER` must not silently implement product code. `CODER` stops at PR. `QA_REVIEWER` and `AUDIO_SCIENCE` may block readiness. `RELEASE_MANAGER` may declare `READY-MTD` but must not infer MTD.

Changes to CI, agent definitions, repository instructions, or release/merge policy should include deterministic validation where practical and must not disable existing analysis/retrieval gates merely to make CI green.