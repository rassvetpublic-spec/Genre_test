# Subagent orchestration external reference for Genre_test

Status: **external R&D reference / architecture hypothesis set; not production truth**
Snapshot date: **2026-08-30**
Relevant areas: agent orchestration, `ai_review`, reviewer independence, context management, parallel research, worktree isolation, evaluation

## Purpose

This document records project-relevant lessons from the Habr article **«Смерть сабагентов в Claude и Codex»** and separates them from claims that still require primary-source verification or local benchmarking.

The article is useful as an architectural warning against automatic multi-agent complexity. It is **not** authoritative documentation for Claude Code, Codex, Anthropic, OpenAI, token accounting, hidden implementation details, or exact performance multipliers.

Recommended role:

```text
EXTERNAL_REFERENCE / HYPOTHESIS SOURCE / BENCHMARK INPUT
```

Not:

```text
PRODUCTION_TRUTH / PRODUCT_API_SPEC / PERFORMANCE_GROUND_TRUTH
```

## Source set

### Secondary source — Habr

Article: «Смерть сабагентов в Claude и Codex»
https://habr.com/ru/articles/1076234/

The article argues that automatic spawning of many cold subagents can create more orchestration overhead than useful work because each worker may need its own context hydration, tool setup, repository reading, status coordination and result handoff.

Treat its exact product internals, limits, token multipliers, polling behavior and anecdotal measurements as **claims to verify**, not repository facts.

### Primary-source support for the narrower architectural principle

Anthropic, Google Cloud Next 2026 session description — **Building Multi-Agent Systems That Actually Work**:
https://www.anthropic.com/events/anthropic-at-google-cloud-next-2026

Anthropic describes multi-agent architectures as powerful but over-applied and identifies three recurring cases where they are useful: **context isolation, parallel execution and specialization**. This supports a conservative Genre_test policy without validating all technical details or numerical claims in the Habr article.

OpenAI — **Introducing the Codex app**:
https://openai.com/index/introducing-the-codex-app/

OpenAI documents separate agent threads and built-in Git worktree support so parallel agents can operate on isolated copies of a repository. This supports worktree-based workspace isolation as a reasonable architecture reference.

## Genre_test architectural hypotheses

The following are project hypotheses to test, not unconditional product rules.

### H1 — minimal agent topology by default

For ordinary bounded tasks, prefer the minimum number of independent LLM contexts needed to achieve the required quality.

Default comparison order:

```text
single warmed agent
-> single agent + independent reviewer
-> multi-agent parallel topology
```

Add another independent agent only when an evaluation demonstrates a useful gain in correctness, coverage, independence or wall-clock time that justifies the added orchestration cost.

### H2 — preserve independent review

`Genre_test` should keep independent reviewer/critic context separate from the implementation/solver context when independent review is part of the quality gate.

Preferred reviewer input:

```text
normalized task contract
+ current diff/proposal
+ tests/evidence
+ explicit acceptance criteria
```

Avoid giving the reviewer the solver's entire conversational history unless that history is itself required evidence. This reduces anchoring and unnecessary context duplication.

This is compatible with the repository's existing rule that the implementation agent must not be the sole reviewer of its own work.

### H3 — do not equate role names with separate agents

A logical role such as `RESEARCHER`, `ARCHITECT`, `CODER`, `QA_REVIEWER`, `AUDIO_SCIENCE` or `RELEASE_MANAGER` does not automatically require a newly spawned cold model session for every transition.

Role separation is an authority/governance concept. Runtime agent/session topology should be chosen independently according to the task and measured evidence.

Where independence is a gate — especially QA or Audio Science review — separate context/model execution remains valuable. Where a transition is only deterministic aggregation or state bookkeeping, another LLM context may add no value.

### H4 — parallelism only for independent work

Parallel agents are strongest when work items are genuinely independent, for example:

- independent research hypotheses;
- separate external source families;
- benchmark variants;
- independent code review or adversarial critique;
- isolated implementation alternatives in separate worktrees.

Do not parallelize tightly sequential work merely because multiple workers are available.

### H5 — use workspace isolation for concurrent code work

When concurrent agents modify code, prefer separate branches/worktrees or otherwise isolated working directories.

Desired invariant:

```text
one active implementation claim
-> one implementation branch
-> isolated workspace for that claim
```

This complements, rather than replaces, the repository's existing Issue/claim/PR collision discipline.

### H6 — measure orchestration overhead explicitly

Future `ai_review` or agent-runtime experiments should capture enough telemetry to compare topologies rather than rely on intuition.

Candidate metrics:

- input/output tokens where exposed by the provider;
- context bytes/tokens supplied per turn;
- wall-clock duration;
- number of model turns;
- retries;
- tool calls;
- handoffs;
- number of independent sessions/workers;
- schema validation failures;
- truncated/incomplete responses;
- provider errors;
- final task quality/eval score.

Provider-specific accounting must remain optional because local Ollama or free-tier providers may expose different usage metadata.

### H7 — incomplete output must fail closed

A result must not be treated as successful merely because a worker/session reports completion.

For structured outputs, validation should cover at least:

```text
transport completed
AND response is parseable
AND schema is valid
AND required fields are present
AND result satisfies task-level completion checks
```

When a provider exposes termination/finish metadata, record it. Detect or conservatively flag truncation where possible.

### H8 — keep subagents for the cases where isolation is the feature

Subagents/isolated workers remain reasonable candidates for:

1. **large raw-output isolation** — search/log/document parsing where returning a compact normalized result protects the main context;
2. **independent review** — critic/reviewer receives a clean artifact without implementation-history anchoring;
3. **wide parallel research** — independent hypotheses or source families where latency matters and duplicated context is bounded;
4. **specialized evidence review** — e.g. independent Audio Science review when that gate is triggered.

The decision should be benchmark-driven rather than ideological: neither "always use agents" nor "never use agents" is a project rule.

## Implications for `ai_review`

The active multi-provider review work should not be changed by this documentation-only task. The following should be considered in a separate implementation Issue after the current `ai_review` work is stable:

- benchmark `single provider` vs `primary + independent reviewer` vs broader multi-agent topology;
- measure quality together with latency/token/context overhead;
- keep reviewer input normalized and independent;
- determine whether synthesis needs a separate model turn or can be deterministic / reuse the primary context;
- make truncation and schema incompleteness explicit failure states;
- persist run telemetry sufficient for topology comparisons.

No current `ai_review` contract is changed by this document.

## Suggested benchmark

Use the same frozen task corpus for all candidate topologies.

```text
Topology A: single agent
Topology B: solver -> independent reviewer -> deterministic resolution when possible
Topology C: solver A + solver B -> cross-review -> synthesis
Topology D: parallel specialized workers -> aggregation
```

Measure:

| Dimension | Example measure |
|---|---|
| correctness | accepted solution / regression rate |
| review value | defects caught only by independent reviewer |
| stability | repeated-run disagreement / schema failure rate |
| cost | tokens or provider usage units where available |
| latency | end-to-end wall time |
| orchestration | turns, retries, handoffs, workers |
| context overhead | duplicated prompt/context volume |
| completeness | truncation/incomplete-result incidence |

A more complex topology should be adopted only when the measured benefit is material for the intended task class.

## Claims from the Habr article that must remain unverified until reproduced

Do **not** copy the following into Genre_test requirements as facts without primary evidence or a local reproducer:

- exact token-cost multipliers;
- exact hidden system-prompt/tool-schema sizes;
- exact cache-hit/cache-expiry rates;
- exact polling intervals or lifecycle behavior across product versions;
- exact agent depth/parallel-worker limits;
- exact output-loss percentages;
- undocumented IPC/socket/message-queue implementation details;
- community anecdotes presented as universal product behavior.

These may be useful research leads.

## Non-goals

- Do not remove the repository's independent QA or Audio Science gates.
- Do not collapse governance roles merely to reduce model calls.
- Do not modify active `ai_review` code from this research note.
- Do not make Claude Code or Codex a required Genre_test runtime dependency.
- Do not treat one vendor's current agent implementation as a permanent architecture constraint.
- Do not optimize only for token count while ignoring correctness, reproducibility or review independence.

## Engineering conclusion

The useful Genre_test lesson is not that subagents are "dead". The useful rule is:

> **Use the minimum agent/session topology that demonstrably improves the target task, preserve true independence where it is a quality gate, and measure the coordination cost.**

For routine sequential work, a warmed single context is the baseline. For review, context isolation can be intentional and valuable. For broad independent research or concurrent implementations, parallel workers can be justified when their work and workspaces are genuinely independent.

This document is a research input for future architecture decisions and benchmarks, not an authorization to change current runtime behavior.