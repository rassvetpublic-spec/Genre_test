# Free-only QA failover policy

Status: proposed governance baseline  
Repository: `rassvetpublic-spec/Genre_test`

## Scope

This document defines the project-wide independent QA fallback contract for autonomous MTD and release work when the primary reviewer is unavailable or rate-limited.

The policy is intentionally **free-only**. The project must not require a payment method, paid subscription, billing account, mandatory prepaid balance, or paid overage to keep the QA pipeline operational.

## Canonical provider order

The preferred independent-review chain is:

1. **Codex** — primary reviewer while available under the existing project integration.
2. **Gemini Developer API / Google AI Studio free tier** — first cloud fallback.
3. **Groq free tier** — second cloud fallback, using an eligible code/reasoning model available on the free plan.
4. **Mistral free tier** — third cloud fallback when an eligible free API allocation is available.
5. **Google Antigravity local/headless free allocation** — workstation fallback when locally available.
6. **Local Ollama + Qwen coder/reasoning model** — final offline/self-hosted fallback.

Provider availability and model names may change. Implementations must discover or configure currently eligible free models without silently enabling paid usage.

## Explicit exclusions

The guaranteed fallback chain must not depend on:

- paid Claude/Anthropic API usage or paid Claude subscriptions;
- DeepSeek API balances that require recharge/payment;
- Kimi paid memberships or paid API balances;
- Vertex AI or another Google Cloud path that requires Cloud Billing;
- any provider feature that requires entering a payment card;
- automatic paid overage, credit purchase, or billing upgrade.

A provider may only be added to the authoritative chain when it has a verified no-payment path consistent with this policy.

## Failover semantics

Failover is allowed only when the current reviewer has **not produced a substantive QA verdict**, for example because of:

- rate limit;
- quota exhaustion;
- service outage;
- authentication/provider unavailability;
- timeout;
- malformed or unverifiable provider output.

If a trusted reviewer returns substantive findings, those findings are blocking. The orchestrator must not switch providers merely to search for a clean `APPROVED` verdict.

## Exact-head and independence guarantees

Every authoritative QA result must be normalized to a provider-independent record bound to the exact 40-character PR head SHA and include sufficient provenance to identify the trusted reviewer/run.

Minimum semantics:

- provider identity;
- trusted reviewer identity or trusted workflow identity;
- repository and PR identity;
- exact reviewed head SHA;
- verdict: `APPROVED`, `CHANGES_REQUESTED`, or `BLOCKED`;
- findings/provenance reference;
- timestamp/run identity.

Stale, ambiguous, spoofed, malformed, conflicting, or incomplete evidence fails closed.

The PR author/implementation agent must remain independent from the authoritative QA reviewer identity.

## One-pass findings closure and MTD

The project workflow is:

1. one substantive independent QA pass;
2. fix the complete findings batch;
3. resolve every finding with machine-verifiable closure evidence bound to the current exact head;
4. run exact-head required CI/security/compatibility checks;
5. perform automatic MTD/merge only when every required gate is green.

A blocked PR must not stop autonomous work on unrelated unblocked Issues/PRs.

No automation may bypass branch protection, required checks, unresolved QA findings, stale-base protection, or explicit QA blocks.

## Cloud secret handling

Cloud fallback credentials must be stored only as GitHub Actions secrets or equivalent protected secret storage. Secrets must not be committed, echoed to logs, passed through PR-controlled code, or exposed to untrusted fork execution.

Workflows consuming secrets must use trusted workflow definitions and must not execute untrusted PR code with privileged credentials.

## Local fallback

Antigravity and Ollama/Qwen are workstation/self-hosted fallback channels. Their use must remain fail-closed and must not invent an independent identity if the same agent that authored the PR is also producing the review.

A local model may be used as advisory pre-review without release authority. To become merge-authoritative, the project must define a trusted self-hosted reviewer identity/workflow and exact-head evidence contract.

Paid-overage options in local tools must remain disabled.

## Autonomous operation

When autonomous project operation is enabled:

- refresh `main`, Issues, PRs, CI/checks and current blockers at the start of each cycle;
- continue unblocked work when another PR is blocked;
- group compatible ready changes into batches;
- merge only when branch protection, exact-head CI and accepted QA evidence permit it;
- report completed work, blockers, batch/merge actions and next priority after every cycle.

## Repository boundary

All new mastering/QA governance work is written to `rassvetpublic-spec/Genre_test`.

`rassvetpublic-spec/OZONE12_MASTERING_LAB` is not a write target for future project records or implementation changes.

## Relationship to existing QA governance

This policy preserves the provider-agnostic/exact-head intent of existing QA governance and one-pass findings-closure work.

Issue #216 remains relevant for provider-agnostic normalization, exact-head evidence, reviewer independence, fail-closed behavior, and findings-no-bypass semantics. Its provider-selection assumptions are superseded only where they conflict with this free-only/no-payment policy.

Issue #215 one-pass findings-closure semantics remain provider-independent.

Existing Codex behavior remains backward-compatible while available.

## Acceptance direction

Implementation work following this policy should cover:

- Codex + at least one cloud-free fallback + one local fallback;
- rate-limit/unavailability failover;
- findings-no-bypass behavior;
- stale-head rejection;
- malformed/spoofed evidence rejection;
- total-provider-exhaustion fail-closed behavior;
- trusted secret handling;
- exact-head CI and independent QA before merge.

AUDIO_SCIENCE: NOT_APPLICABLE
