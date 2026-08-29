---
applyTo: ".github/**,AGENTS.md,docs/AGENT_WORKFLOW.md"
---

Repository workflow changes must preserve the Agent System v2 authority model and lifecycle:

```text
REQUEST -> SCOPED -> optional ARCHITECTURE-READY -> CLAIMED -> IMPLEMENTING
-> REVIEW -> VALIDATION -> READY-MTD <head-sha> -> MTD-authorized merge
-> MERGED -> POST-MERGE-VERIFIED -> CLOSED
```

Stop/escalation states include `BLOCKED`, `NEEDS-EVIDENCE`, `AMENDMENT-REQUIRED`, and `NEEDS-USER-APPROVAL`.

Do not weaken or bypass these rules:

- never commit directly to `main`;
- GitHub Issues remain task contracts; chat memory is not a required shared-state layer;
- before implementation, check for duplicate/overlapping active Issue/branch/PR scope;
- one implementation task must not silently create competing active implementation branches/PRs;
- new/material architecture, product, safety, breaking-contract, or release-policy decisions require explicit user approval;
- `CODER` is the production implementation role and stops at PR;
- `QA_REVIEWER` produces an exact-head software verdict, not READY-MTD;
- `AUDIO_SCIENCE` produces an exact-head domain verdict when triggered, not READY-MTD;
- `RELEASE_MANAGER` aggregates independent gates; it must not replace missing QA/Audio Science with its own second review;
- only `RELEASE_MANAGER` may declare `READY-MTD <40-char-sha>` or execute merge/merged-head deletion;
- the user has granted standing automatic MTD for this project, so an already approved-scope PR may be merged automatically by RELEASE_MANAGER after exact-head READY-MTD without a fresh token;
- explicit `mtd`, `MTD`, or `мтд` remains a valid one-off/scoped override;
- standing/sequential MTD authority never covers unrelated work, silent scope expansion, missing/inconclusive evidence, or a new architecture/product/safety/release decision;
- every PR in a train must independently pass exact-head READY-MTD/current-head validation;
- any PR head SHA change invalidates prior exact-head QA/Audio/readiness evidence;
- after every merge, verify CI/test state on `main`; only RELEASE_MANAGER may explicitly delete the merged head branch before continuing;
- REPO_STEWARD is report-only for leftover branches and has no branch-delete authority;
- stop an automatic/sequential merge train on CI failure, conflict, unexpected scope, missing/inconclusive evidence, changed head without revalidation, or a new decision point;
- do not delete unmerged branches with unique commits, open PRs, or unclear ownership;
- do not enable GitHub auto-merge as a substitute for governed readiness/MTD authority.

Custom agents must use least-privilege intent and explicit contract sections for responsibilities, permissions, inputs, outputs, handoff, evidence, stop conditions, GitHub authority, and MTD interaction.

Changes to CI, agent definitions, repository instructions, or release/merge policy should include deterministic validation where practical and must not disable existing analysis/retrieval gates merely to make CI green. The stronger structural machine-checkable contract gate belongs to the dedicated Agent System v2 CI PR rather than ad-hoc natural-language parsing.
