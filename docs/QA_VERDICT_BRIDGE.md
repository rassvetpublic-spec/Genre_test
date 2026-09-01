---
title: "QA Verdict Bridge"
doc_type: protocol
area: agents
status: canonical
summary: "Fail-closed exact-head normalization contract for independent GitHub Codex clean-review evidence into the qa-verdict-bridge commit status."
tags:
  - область/agents
  - тип/protocol
  - статус/canonical
---

# QA Verdict Bridge

## Purpose

`qa-verdict-bridge` is a narrow repository-owned adapter for one problem: GitHub Codex can provide an independent exact-head code review as prose, while Genre_test release governance consumes deterministic exact-head QA evidence.

The bridge converts only the explicitly recognized Codex clean-review signal into a normalized commit status. It does not perform code review, does not decide merge readiness, does not merge, and does not normalize Audio Science evidence.

Canonical invariant:

```text
independent review evidence
-> deterministic exact-head normalization
-> qa-verdict-bridge commit status
-> RELEASE_MANAGER evidence aggregation
```

## Request binding

A bridge-eligible review request is a PR conversation comment containing both:

```text
@codex review
QA_REQUEST_HEAD: <40-char-current-pr-head-sha>
```

The bound SHA must still equal the current PR head when the bridge evaluates evidence. A head change invalidates prior status because every status is written to one commit only.

Evidence ordering uses the latest GitHub mutation time (`updated_at` when present, otherwise `created_at`). When request and response share the same effective GitHub timestamp, issue-comment database IDs provide strict top-level ordering. Cross-surface evidence with an indistinguishable timestamp is treated conservatively rather than guessed into approval. Editing an old request therefore cannot make an earlier clean response count as a response to that newly mutated request.

## Accepted reviewer identity

Initial provider set is deliberately fixed:

```text
chatgpt-codex-connector[bot]
chatgpt-codex-connector
```

The configured reviewer identity cannot also be the PR author. Other bots, humans, AI providers, or arbitrary prose are not normalized by this bridge.

## Recognized clean signal

The clean-review signal must contain the fixed Codex phrase:

```text
Codex Review: Didn't find any major issues.
```

and a reviewed commit marker:

```text
**Reviewed commit:** `<sha-prefix>`
```

The prefix must resolve through GitHub to one exact 40-character commit SHA, and that SHA must equal the current PR head.

## Fail-closed decision rules

`success` is allowed only when all required evidence is present and unambiguous:

1. an exact current-head request exists;
2. a strictly subsequent configured Codex response exists using mutation-aware ordering;
3. the response contains the recognized clean phrase and reviewed-commit marker;
4. the reviewed prefix resolves to the exact current head;
5. the PR author is not the configured Codex reviewer identity;
6. no unresolved review thread remains;
7. no newer top-level Codex evidence or review-thread evidence supersedes the clean signal;
8. required GitHub API evidence is complete and parseable;
9. paginated review-thread evidence is either fully retrieved or rejected as incomplete rather than silently truncated.

Missing review completion stays `pending`. Actionable review evidence becomes `failure`. Ambiguous or incomplete evidence becomes `error`. No ambiguous state is converted into approval.

If live evidence collection fails after the exact current head is known, the bridge best-effort writes `qa-verdict-bridge=error` with `QA_BLOCKED <sha>` before failing the workflow. If GitHub itself prevents that status write, the workflow still fails non-zero and cannot create approval evidence.

## Evidence mutation invalidation

A durable success must be re-evaluated when review evidence can change. The workflow therefore reacts to:

- `pull_request_target` head/open/reopen/ready changes;
- PR `issue_comment` create/edit/delete;
- `pull_request_review` submit/edit/dismiss;
- `pull_request_review_comment` create/edit/delete.

All of these executions explicitly check out trusted default-branch bridge code. Event payload text is never executed. Deleting or editing the bound request, clean result, or review evidence cannot intentionally preserve an old success without a fresh live evaluation.

## Commit status contract

The only durable write is the commit status context:

```text
qa-verdict-bridge
```

Normalized states:

| GitHub state | Marker | Meaning |
|---|---|---|
| `success` | `QA_APPROVED <40-char-sha>` | Recognized independent exact-head clean review |
| `failure` | `QA_CHANGES_REQUESTED <40-char-sha>` | Actionable/stale/superseded review evidence |
| `error` | `QA_BLOCKED <40-char-sha>` | Evidence or API evaluation is ambiguous/incomplete |
| `pending` | `QA_BLOCKED <40-char-sha>` | Exact-head review is requested but not complete |

This status is QA evidence only. It is not `READY-MTD` and carries no merge authority.

## Workflow security boundary

The workflow runs only trusted default-branch bridge code for `pull_request_target`, PR `issue_comment`, `pull_request_review`, and `pull_request_review_comment` events.

Permissions are restricted to:

```text
contents: read
pull-requests: read
issues: read
statuses: write
```

The workflow must not:

- check out or execute PR-head code;
- grant contents, PR, or Issue write permission;
- run shell/code supplied by PR content or comment bodies;
- mutate files, branches, comments, reviews, labels, or merge state;
- obtain PR head identity from untrusted text instead of the GitHub API.

The only untrusted-text operation is deterministic parsing of already retrieved review/request evidence.

## Release Manager consumption

After this bridge is merged and post-merge verified, `QA_REVIEWER` evidence may be satisfied by either:

1. an explicit approved independent exact-head `QA_APPROVED <sha>` marker; or
2. `qa-verdict-bridge=success` written to that exact SHA by this repository adapter.

`RELEASE_MANAGER` still performs the normal readiness aggregation: exact current SHA, CI, scope, review-thread state, mergeability, required Audio Science evidence when applicable, unresolved risks, and then `READY-MTD <sha>`.

A status on any older commit is irrelevant after the PR head moves.

## Bootstrap limitation

The Issue #171 implementation PR cannot use the unmerged bridge to attest itself. It must obtain independent substantive QA through the pre-existing governance path. Only after merge and post-merge verification may later PRs consume `qa-verdict-bridge` as normalized QA evidence.

## Audio Science boundary

The bridge never normalizes or substitutes `AUDIO_SCIENCE`. Audio/DSP/mastering/Ozone/listening-methodology changes still require their independent exact-head Audio Science verdict under `AGENTS.md`.

## Non-goals

- generic LLM prose interpretation;
- multi-provider review arbitration;
- review generation;
- GitHub merge automation;
- branch mutation;
- comment/review mutation;
- Audio Science normalization;
- Product MCP runtime;
- product, retrieval, DSP, mastering, or workstation behavior changes.
