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
- the unresolved roadmap decision.

The detailed implementation assignment lives in [`MCP_IMPLEMENTATION_TASK.md`](MCP_IMPLEMENTATION_TASK.md).

---

## 2. MCP in one sentence

**Model Context Protocol (MCP) is a standard way for an AI application to discover and use external context and capabilities through typed protocol contracts.**

A useful analogy is USB-C for AI integrations: instead of every AI client learning every program's private commands, a program can expose a standardized MCP interface.

For Genre_test, the target idea is:

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

For Genre_test:

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

MCP should sit **above** those stable service boundaries:

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

## 9. Mental experiment: what changes after MCP?

### Before MCP

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

### After a well-designed MCP layer

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

Conceptually:

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

## 11. Proposed Genre_test MCP boundary

Target principle:

> Keep the MCP server thin. Domain/business logic belongs in reusable Genre_test services, not in MCP handlers.

Conceptual project layout:

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

Exact paths are not approved until Phase 0 inventory confirms the real service boundaries.

The adapter must not create a second implementation of:

- audio analysis;
- retrieval;
- QC metrics;
- mastering heuristics;
- Ozone parameter semantics;
- GitHub governance.

---

## 12. Proposed read-only-first MVP

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

Prompts are not required for the first Genre_test MCP MVP.

If added later, they should represent useful explicit user-controlled workflows, not hidden policy or automatic agent behavior.

---

## 13. Why read-only first

Read-only-first provides evidence that:

- the adapter can discover and expose project capabilities correctly;
- schemas are usable;
- core/service boundaries are stable enough;
- errors are structured;
- local transport works on Windows;
- results match direct internal calls;
- the MCP layer does not silently change audio/retrieval semantics.

Only after that evidence should repository writes, render requests or release operations be considered.

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

Preferred design:

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

MCP cannot override `AGENTS.md` or the GitHub Ruleset.

---

## 15. Local-first transport direction

Because Genre_test is Windows-local and Python-first, **stdio is the leading MVP transport candidate**:

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

This is a proposal, not a locked implementation decision. Phase 0 must confirm official Python SDK compatibility and the chosen client's requirements.

For stdio, logs must go to stderr rather than corrupting protocol stdout.

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

It should be an interface over those contracts, not a replacement.

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

---

## 19. Costs and responsibilities

MCP also creates a new public-ish internal contract that must be maintained.

Avoid tool proliferation such as:

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

---

## 20. Roadmap status

Current `ROADMAP.md` places:

> optional MCP façade only after stable APIs exist

under **v0.9 — ComfyUI, runtime and automation**.

This document does **not** move MCP earlier.

The unresolved user decision is:

```text
A. Keep production MCP implementation in v0.9 after stable local APIs exist.

or

B. Promote a small read-only MCP infrastructure track earlier,
   without accelerating future repair/mastering product scope.
```

Until the user explicitly chooses, current roadmap placement remains authoritative.

---

## 21. Architecture acceptance gate before implementation

Production MCP code should not start until an implementation task confirms:

- inventory of reusable Genre_test services vs CLI-only boundaries;
- chosen protocol revision and official SDK version;
- local transport choice;
- resource/tool schemas;
- error contract;
- filesystem/path policy;
- permission groups;
- smoke/contract/security test strategy;
- no generic arbitrary execution capability;
- explicit roadmap placement authorization.

See [`MCP_IMPLEMENTATION_TASK.md`](MCP_IMPLEMENTATION_TASK.md) for the proposed execution contract.
