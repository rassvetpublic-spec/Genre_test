# Rules Hub interoperability baseline

Status: **ACCEPT_WITH_CHANGES / docs-contract only**
Issue: **#178**

This document is the Genre_test owner for the accepted interoperability boundary with `rassvetpublic-spec/rassvet-rules-hub`.

## Core invariant

> **ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS**

Interoperability means compatible vocabulary and provenance, not shared authority. Each Git repository remains the authority boundary for its own canonical state.

## Provenance and pinning

The architecture decision in Issue #178 reviewed the Rules Hub proposal at immutable repository revision:

```text
687b17e68ecf2cfd41dae33b70079eb24ef4c69d
```

The accepted source document is:

```text
docs/GENRE_TEST_INTEROPERABILITY_PROPOSAL.md
```

A live refresh on 2026-08-31 found Rules Hub `main` at:

```text
4df36c3db64d813a4688e481226bab9bc30ebab2
```

The proposal blob is unchanged across those two revisions (`8e50e35f4c5411fa08eadfdad9314f69e6da84e7`). The live branch name is never an interoperability dependency: cross-project checks must use immutable revisions or checked-in fixtures/profiles, never live `peer/main`.

## Shared vocabulary

The compatible layer may use the following common concepts:

```text
doc_type
status
typed relations
provenance
```

Knowledge ownership classes have the same intended meaning in compatibility material:

```text
canonical_document
canonical_machine_state
generated_projection
derived_index
visualization
```

Project-local fields remain project-local. In particular, `area`, domain registries, product capabilities and specialized lifecycle fields do not become globally owned vocabulary merely because both repositories can read them.

## Genre_test canonical owners

Interoperability does not supersede these owners:

### Governance

```text
AGENTS.md
docs/AGENT_WORKFLOW.md
```

Exact-head QA, AUDIO_SCIENCE, READY-MTD, merge authorization and branch-cleanup rules remain entirely Genre_test governance. Issue #171 remains the separate task for a permanent independent-review-to-formal-QA bridge; interoperability must not normalize or invent QA markers.

### Obsidian / knowledge navigation

```text
docs/obsidian/IMPLEMENTATION.md
docs/obsidian/KNOWLEDGE_REGISTRY.json
tools/obsidian_knowledge_sync.py
```

The global registry has `knowledge_navigation_metadata_only` authority. It is a navigation layer, not a second source of technical, governance, research, runtime or mastering truth. Obsidian/plugins/CLI are views or consumers, not owners.

### Research Radar

Canonical process:

```text
docs/research/RESEARCH_OPERATING_RULES.md
docs/research/RESEARCH_RADAR.md
```

Canonical mutable state:

```text
docs/research/data/*.json
```

Generated projections:

```text
docs/research/obsidian/**
docs/development/research_radar/**
```

Rules Hub may reuse the structural pattern, but it must not share, mirror as mutable truth, or mutate Genre_test Radar topics/state/runs. The mutable direction remains one-way: `JSON -> generated Markdown`.

### MCP

Genre_test MCP decisions remain owned by their dedicated MCP documents, issues and PRs. Open PR #157 currently proposes a Track Q / Track P split; this interoperability baseline neither accepts that proposal on behalf of #157 nor supersedes it. It does **not** authorize `src/genre_test/mcp/**`, an MCP runtime, a shared cross-repository server, shared tools, or write capability into either peer repository. Interoperability work must not preempt the dedicated MCP track/PR.

## Authority boundaries

The following are forbidden by this baseline:

- Rules Hub overriding Genre_test `AGENTS.md`, architecture, active state, subsystem contracts or mutable project state;
- Genre_test overriding Rules Hub canonical state;
- one shared mutable Vault;
- one shared mutable Research Radar state;
- bidirectional JSON/Markdown state synchronization;
- one shared MCP server or one mandatory shared Tool set;
- direct cross-repository mutation through an interoperability adapter;
- tests whose result changes merely because the peer repository's live `main` moved.

The compatible operating model is:

```text
pinned source/profile/fixture
        |
        v
shared vocabulary + provenance semantics
        |
        +--> Genre_test canonical owners
        +--> Rules Hub canonical owners
```

## Provenance envelope

Where a cross-project view or future compatibility fixture exposes data, it should preserve enough provenance to identify its owner without creating new authority, for example:

```text
repository
path
revision
classification / ownership class
```

For machine-facing results, compatible conventions may additionally include narrow fields such as `ok`/`status` and `error.code`/`error.message`. URI namespaces and Tool names are intentionally allowed to differ between projects.

## Intentional differences

Compatibility does not require identical:

- `area` values or domain-specific metadata;
- document inventories;
- Radar topic/state/run contents;
- MCP URI namespaces, Resources or Tools;
- product roadmaps or active milestones;
- governance implementations beyond explicitly shared vocabulary semantics.

## Future contract tests

Any cross-project compatibility tests must be deterministic and hermetic. They may consume:

1. an immutable peer commit/profile; or
2. a checked-in fixture derived from a named immutable revision.

They must not query live Rules Hub `main` in CI and must not mutate either repository.

## Scope of #178

This baseline is documentation/contract only. It changes no runtime, Research Radar mutable state, product roadmap, audio/DSP semantics or MCP implementation.

`AUDIO_SCIENCE: NOT_APPLICABLE`
