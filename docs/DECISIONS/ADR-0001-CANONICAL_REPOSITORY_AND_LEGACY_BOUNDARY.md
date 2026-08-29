# ADR-0001: Canonical Repository and Legacy Boundary

Status: **accepted**

## Context

The historical OZONE12_MASTERING_LAB contains reusable mastering knowledge, XML maps, tools and validation lessons, while active engineering has moved to Genre_test.

Maintaining two writable project truths would create conflicting architecture and stale rules.

## Decision

- `Genre_test/main` is the canonical project truth.
- `OZONE12_MASTERING_LAB` is frozen legacy reference.
- No new commits, branches, PRs, issues or architecture changes are created in the legacy repository.
- Reusable legacy knowledge is normalized into Genre_test docs/code/tests.
- The archived Universal Core v1.4.1 remains evidence for exact historical artifacts.

## Consequences

Positive:

- one engineering source of truth;
- legacy knowledge remains accessible without governing current code;
- decisions can evolve without rewriting historical evidence.

Cost:

- imported rules must state whether they are schema facts, heuristics, historical procedures or track-specific evidence.

## Validation

A future change violates this ADR if it requires writing new active development state back into OZONE12_MASTERING_LAB.
