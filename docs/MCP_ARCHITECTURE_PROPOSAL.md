# Model Context Protocol (MCP) — architecture proposal for Genre_test

Status: **architecture/documentation proposal; no production MCP implementation authorized by this document**  
Related Issue: **#146**  
Protocol revision checked: **2026-07-28**  
Source provenance: [`MCP_SOURCE_REGISTRY.md`](MCP_SOURCE_REGISTRY.md)

## 1. Why this document exists

This document preserves the project-relevant MCP reasoning that was previously discussed in chat so a new repository-aware agent can recover it from GitHub without relying on conversation memory.

It explains:

- MCP in plain language;
- the important terms;
- the current `2026-07-28` protocol model;
- what MCP would change for Genre_test;
- what MCP would **not** change;
- the proposed adapter boundary;
- the read-only MVP idea;
- security limits;
- the selected Track Q / Track P roadmap split.

The detailed Product MCP implementation assignment lives in [`MCP_IMPLEMENTATION_TASK.md`](MCP_IMPLEMENTATION_TASK.md).

---

## 2. MCP in one sentence

**Model Context Protocol (MCP) is a standard way for an AI application to discover and use external context and capabilities through typed protocol contracts.**

A useful analogy is USB-C for AI integrations: instead of every AI client learning every program's private commands, a program can expose a standardized MCP interface.

For Genre_test, the product-side target idea is:

```text
AI / Agent
    |
    v
Genre_test MCP adapter
    |
    +--> existing Genre_test services / CLI boundaries
    +--> analysis / retrieval / QC
    +--> REAPER / Ozone orchestration when later appropriate
```

MCP is **not** the audio engine. It is the interface layer.

---

## 3. Plain-language glossary

| Term | Plain meaning | Genre_test example |
|---|---|---|
| **MCP** | Standard rules for AI applications to talk to external systems | A standard AI-facing interface for Genre_test |
| **Host** | The AI application/container coordinating everything | Chat/IDE/agent runtime that connects to Genre_test |
| **Client** | The Host-side connector that talks MCP to one server | The connector instance attached to Genre_test MCP |
| **Server** | A service exposing context/capabilities via MCP | `Genre_test MCP server` |
| **Tool** | An executable function the model can invoke | `analyze_audio(...)`, `runtime_doctor()` |
| **Resource** | Context/data exposed through a URI contract | `genre-test://project/active-current` |
| **Prompt** | Reusable server-provided prompt template, intended to be user-controlled | A future explicit `review-analysis` template, if useful |
| **Capability** | A declared feature the client/server supports | Tools, resources, prompts, subscriptions |
| **Schema** | Formal definition of valid input/output structure | `run_id: string`, `suite: enum` |
| **Context** | Information made available to the model for the current task | Project status, QC result, analysis result |
| **API** | Programmatic interface of a concrete backend | Python function, REST endpoint, GitHub API |
| **CLI** | Command-line interface | `genre-test ...` or a PowerShell launcher |
| **Backend** | The system doing the real work | Genre_test analysis/retrieval/mastering code |
| **Agent** | AI logic that decides what to do next | `CODER`, `QA_REVIEWER`, `AUDIO_SCIENCE` |
| **Authentication** | Proving who the caller is | OAuth/token/local process identity |
| **Authorization** | Deciding what the caller may do | Read-only vs repo-write/release capability |
| **Transport** | How MCP messages physically move | Local stdio; later possibly network transport |
| **JSON-RPC 2.0** | Structured request/response message format used by MCP | Wire format handled by the MCP SDK |

Two short rules avoid most confusion:

```text
Agent decides WHAT to do.
MCP defines HOW capabilities are exposed.
Genre_test core performs the real work.
```

And:

```text
Resource = context/data to read.
Tool     = action/function to execute.
Prompt   = reusable user-controlled template.
```

---

## 4. Important 2026-07-28 protocol model

Older MCP tutorials can be misleading because the protocol changed materially.

For the checked revision `2026-07-28`:

- the protocol core is **stateless**;
- requests are self-contained;
- protocol version and client capabilities travel with every modern request;
- modern MCP does not depend on the old protocol-level session/`initialize` handshake model;
- servers must implement `server/discover` for supported versions/capabilities/identity discovery;
- clients are not required to call discovery as a mandatory first action;
- legacy initialization-based behavior remains compatibility context for older revisions.

Therefore a new Genre_test implementation must not copy an old tutorial and accidentally build its architecture around a persistent MCP session or mandatory legacy `initialize` lifecycle.

See [`MCP_SOURCE_REGISTRY.md`](MCP_SOURCE_REGISTRY.md) for the versioning/changelog sources.

---

## 5. Host / Client / Server model

The conceptual structure is:

```text
USER
  |
  v
HOST (AI application / agent runtime)
  |
  +--> MCP Client A <--> MCP Server A
  |
  +--> MCP Client B <--> MCP Server B
  |
  +--> MCP Client C <--> MCP Server C
```

For the future Genre_test product façade:

```text
AI Host
  |
  v
MCP Client
  |
  v
Genre_test MCP Server
  |
  v
Genre_test core/services
```

Important security property from the MCP architecture: the Host is the coordinator. A server should receive only the context necessary for its task and should not automatically see the user's entire conversation or other servers.

---

## 5A. Two separate Genre_test MCP tracks

The project distinguishes two MCP use cases that have different timelines and dependency directions.

### Track Q — QA evidence consumption

```text
QA Orchestrator / Host
        |
        +--> Evidence Source
        |      +--> GitHub
        |      +--> local deterministic checks
        |      +--> future GitHub MCP
        |      +--> future Rules Hub MCP
        |
        v
immutable ReviewEvidencePack
        |
        v
reviewers
```

Track Q is consumer-side engineering infrastructure.

It does not expose Genre_test product capabilities through an MCP server.

The evidence contract must be independent of MCP transport so direct/local evidence sources may exist before MCP adapters are ready. The first Track Q implementation therefore does not require MCP runtime or SDK dependencies merely to define or test `ReviewEvidencePackV1`.

Track Q is read-only from repository/governance perspective unless a later separate write-capability task is explicitly approved. Models do not receive repository merge, release, direct-main, force-push or arbitrary execution authority.

### Track P — Product MCP façade

```text
AI / MCP Host
        |
        v
Genre_test MCP Server
        |
        v
stable Genre_test services
```

Track P remains a **v0.9** product/runtime direction, after stable local service/API boundaries exist.

The two tracks must not share authority merely because both use MCP terminology. Starting Track Q does not authorize `src/genre_test/mcp/**`, Product MCP tools, or product-scope acceleration.

---

## 6. MCP is not an API replacement

Genre_test already has or will have concrete implementation interfaces:

```text
Python functions
CLI commands
PowerShell scripts
GitHub API calls
REAPER invocation
Ozone XML/preset contracts
```

Product MCP should sit **above** those stable service boundaries:

```text
Agent
  |
  v
MCP Tool: analyze_audio(...)
  |
  v
Genre_test service/API/CLI adapter
  |
  v
real analysis pipeline
```

The MCP adapter may call a Python service, CLI, subprocess or API internally. The agent should not need to know which one.

This creates a useful abstraction boundary:

```text
Before MCP:
agent knows HOW Genre_test is wired internally.

After MCP:
agent knows WHAT Genre_test can do.
```

---

## 7. MCP is not an agent

MCP does not reason, plan or decide priorities.

Bad model:

```text
MCP = autonomous AI worker
```

Correct model:

```text
Agent = reasoning / planning / policy
MCP   = typed capability interface
Core  = implementation
```

A weak agent remains weak after MCP. MCP improves execution boundaries, discoverability, validation, interoperability and access control; it does not improve the agent's intelligence.

---

## 8. MCP is not project memory

MCP can expose memory or retrieval systems, but MCP itself is not memory.

Example:

```text
Agent
  |
  v
MCP resource/tool
  |
  v
project database / source registry / run history
```

The canonical project knowledge still belongs in GitHub files, Issues, versioned databases/artifacts and explicitly defined stores. MCP only exposes selected knowledge through a standard interface.

---

## 9. Mental experiment: what changes after Product MCP?

### Before Product MCP

An AI worker may need to know:

```text
where the repo lives
which Python entrypoint to call
which PowerShell script to run
how the CLI formats output
where run JSON is written
how REAPER is invoked
which temp directory is used
how QC data is encoded
```

Different agents may duplicate this knowledge.

```text
RESEARCHER --> its own project access logic
CODER      --> its own git/test logic
QA         --> its own test/result parsing
AUDIO      --> its own analysis/runtime invocation
RELEASE    --> its own repository integration
```

### After a well-designed Product MCP layer

Agents can depend on stable capabilities:

```text
get_project_status()
runtime_doctor()
analyze_audio()
get_analysis_result()
get_qc_report()
compare_runs()
run_tests()
```

The implementation detail stays behind the adapter.

If a backend command later changes from:

```text
python -m genre_test analyze ...
```

to another internal service, the external MCP tool can remain:

```text
analyze_audio(...)
```

Only the adapter/service integration changes.

That is the major architectural value: **decoupling AI consumers from internal implementation details**.

---

## 10. What changes for the multi-agent system

Current specialized roles remain:

- `REPO_STEWARD`
- `RESEARCHER`
- `ARCHITECT`
- `CODER`
- `QA_REVIEWER`
- `AUDIO_SCIENCE`
- `RELEASE_MANAGER`

MCP must not duplicate those roles as tools.

Do **not** create interfaces such as:

```text
coder_agent_tool()
architect_tool()
qa_agent_tool()
```

Expose domain capabilities instead:

```text
project_status
analysis
QC
test execution
run comparison
later: bounded render / work-session operations
```

Conceptually for Track P:

```text
                 RESEARCHER
                 ARCHITECT
                 CODER
                     \
                      \
                  Genre_test MCP
                      /
                     /
                 QA_REVIEWER
                 AUDIO_SCIENCE
                 RELEASE_MANAGER
                        |
                        v
                 Genre_test core
```

The role/policy layer determines which capabilities a given agent is allowed to use.

---

## 11. Proposed Genre_test Product MCP boundary

Target principle:

> Keep the MCP server thin. Domain/business logic belongs in reusable Genre_test services, not in MCP handlers.

Conceptual project layout for Track P:

```text
Genre_test/
  src/genre_test/
    ... core/service modules ...
    mcp/
      server.py
      tools.py
      resources.py
      schemas.py
      errors.py
      policy.py
```

Exact paths are not approved until the Product MCP implementation gate confirms the real service boundaries.

The adapter must not create a second implementation of:

- audio analysis;
- retrieval;
- QC metrics;
- mastering heuristics;
- Ozone parameter semantics;
- GitHub governance.

Track Q does not use this `src/genre_test/mcp/**` boundary.

---

## 12. Proposed Product MCP read-only-first MVP

### Resources

Candidate stable resources:

```text
genre-test://project/active-current
genre-test://project/roadmap
genre-test://project/architecture
genre-test://project/source-registry
genre-test://project/version
genre-test://runtime/status
```

A resource must return canonical project data or an explicit not-available result. It must not invent state.

Do not expose a generic arbitrary-path resource such as:

```text
read_file(path="C:\\anything\\...")
```

### Tools

Candidate MVP tools:

```text
get_project_status()
runtime_doctor()
analyze_audio(audio_path, profile)
get_analysis_result(run_id)
get_qc_report(run_id)
compare_runs(left_run_id, right_run_id)
run_tests(suite)
```

`run_tests` must select from approved suites; it must not accept an arbitrary shell command.

### Prompts

Prompts are not required for the first Genre_test Product MCP MVP.

If added later, they should represent useful explicit user-controlled workflows, not hidden policy or automatic agent behavior.

---

## 13. Why Product MCP is read-only first

Read-only-first provides evidence that:

- the adapter can discover and expose project capabilities correctly;
- schemas are usable;
- core/service boundaries are stable enough;
- errors are structured;
- local transport works on Windows;
- results match direct internal calls;
- the MCP layer does not silently change audio/retrieval semantics.

Only after that evidence should repository writes, render requests or release operations be considered.

Track Q is independently read-only and does not depend on this Product MCP milestone.

---

## 14. Security model

A major MCP risk is turning a typed interface into unrestricted remote/local code execution.

Rejected design:

```text
run_shell(command: string)
run_powershell(script: string)
read_any_file(path: string)
write_any_file(path: string)
git_force_push(...)
```

Preferred bounded Product MCP design:

```text
runtime_doctor()
run_tests(suite="default")
analyze_audio(...)
request_render(session_id)
create_work_branch(name)
```

Narrow tools make inputs testable and permissions understandable.

Genre_test-specific hard rules:

1. No arbitrary shell capability.
2. No unrestricted filesystem capability.
3. No direct writes to `main`.
4. No force push.
5. No secrets/private keys/tokens stored in the repo or exposed as resources.
6. Validate canonical paths and prevent traversal.
7. Preserve source-audio immutability.
8. Keep measured/model/user-entered/derived evidence distinct.
9. Treat tool metadata/description as untrusted when it does not come from a trusted server.
10. Remote/protected MCP requires a separate authorization/security review.
11. Track Q models receive frozen evidence, not repository mutation authority.

MCP cannot override `AGENTS.md` or the GitHub Ruleset.

---

## 15. Local-first Product MCP transport direction

Because Genre_test is Windows-local and Python-first, **stdio is the leading Track P MVP transport candidate**:

```text
AI Host
  |
launches local subprocess
  |
  v
Genre_test MCP server
  |
stdin/stdout JSON-RPC
```

Reasons:

- canonical MCP local transport;
- no network listener required for the first MVP;
- natural fit for a local Python process;
- simpler security boundary than introducing a remote server immediately.

This is a proposal, not a locked implementation decision. Product MCP Phase 0 must confirm official Python SDK compatibility and the chosen client's requirements.

For stdio, logs must go to stderr rather than corrupting protocol stdout.

Track Q evidence collection remains transport-independent and is not required to use this stdio design.

---

## 16. Error and output philosophy

Agents should not need to parse human console prose.

Bad external contract:

```text
"Everything looks mostly okay, maybe REAPER was not found..."
```

Preferred:

```json
{
  "ok": false,
  "error": {
    "code": "RUNTIME_NOT_READY",
    "message": "REAPER runtime is not available.",
    "details": {"check": "reaper"}
  }
}
```

Stable machine-readable output is one of the reasons to add MCP at all.

---

## 17. What MCP does not change in the project

MCP does not change:

- the audio truth model;
- immutable-source policy;
- v0.5 retrieval architecture;
- v0.6 repair semantics;
- Ozone module-order semantics;
- REAPER as the Ozone render host;
- branch -> PR -> CI -> exact-head QA -> READY-MTD governance;
- the seven-agent role model;
- GitHub as the engineering source of truth.

Track Q and Track P are interfaces/infrastructure over those contracts, not replacements.

---

## 18. Expected benefits

If implemented correctly, MCP should provide:

1. **Less coupling** — agents do not depend on internal commands/paths.
2. **One capability vocabulary** — different AI clients see the same operations.
3. **Safer autonomy** — narrow typed tools replace generic shell access.
4. **Better testability** — input/output/error contracts can be unit/contract tested.
5. **Easier backend evolution** — internals can change behind a stable interface.
6. **Client portability** — another MCP-aware host can use the same Genre_test interface.
7. **Cleaner agent prompts** — role prompts contain policy/decision logic rather than duplicated command recipes.
8. **Reproducible QA evidence** — Track Q can bind reviewers to one frozen exact-head evidence set independently of Product MCP readiness.

---

## 19. Costs and responsibilities

MCP also creates public-ish internal contracts that must be maintained.

Avoid Product MCP tool proliferation such as:

```text
analyze_v1
analyze_new
analyze_final
analyze2
```

A stable tool needs:

- clear name;
- input schema;
- output schema;
- error contract;
- side-effect classification;
- permission classification;
- compatibility/versioning rule;
- tests.

The adapter is only valuable if it is more stable and safer than direct ad-hoc command execution.

For Track Q, the durable contract is the review-evidence schema and source provenance, not a requirement that every source use MCP.

---

## 20. Roadmap decision — Option C

The previous A/B roadmap question is resolved by separating the use cases.

### Selected direction

```text
Track Q:
read-only QA evidence consumption may begin earlier.

Track P:
Genre_test product MCP façade remains in v0.9.
```

This is not an acceleration of the Genre_test product MCP server.

Track Q must first establish a transport-independent evidence contract and Evidence Source abstraction. MCP is one possible evidence transport, not a prerequisite for the first EvidencePack implementation.

Track Q must not introduce:

- `src/genre_test/mcp/**` product-server implementation;
- Analyze/Retrieval/QC/Repair/Mastering MCP product tools;
- repository write authority;
- merge/release authority;
- arbitrary shell/filesystem capabilities.

The first implementation step after this architecture decision is the canonical exact-head `ReviewEvidencePackV1` contract tracked by Q1.

---

## 21. Architecture acceptance gates

### Track Q next gate

Before QA evidence implementation expands beyond Q1, its task contract must define:

- canonical `ReviewEvidencePackV1` content and versioning;
- exact-head binding;
- deterministic serialization/content identity;
- separation of content identity from run metadata such as `collected_at` and `run_id`;
- source provenance and missing/unknown evidence semantics;
- no mandatory MCP runtime or provider dependency for Q1;
- no GitHub write capability.

### Track P implementation gate

Production Product MCP code should not start until an implementation task confirms:

- v0.9/stable-service timing remains appropriate;
- inventory of reusable Genre_test services vs CLI-only boundaries;
- chosen protocol revision and official SDK version;
- local transport choice;
- resource/tool schemas;
- error contract;
- filesystem/path policy;
- permission groups;
- smoke/contract/security test strategy;
- no generic arbitrary execution capability;
- no overlapping implementation Issue/branch/PR.

See [`MCP_IMPLEMENTATION_TASK.md`](MCP_IMPLEMENTATION_TASK.md) for the proposed Track P execution contract.
