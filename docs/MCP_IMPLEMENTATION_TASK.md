# Technical task: implement Genre_test Product MCP façade

Status: **planned task; implementation is not authorized merely by this file**  
Track: **Product MCP / Track P**  
Roadmap: **v0.9**  
Related Issue: **#146**  
Protocol baseline checked: **MCP 2026-07-28**  
Architecture: [`MCP_ARCHITECTURE_PROPOSAL.md`](MCP_ARCHITECTURE_PROPOSAL.md)  
Sources: [`MCP_SOURCE_REGISTRY.md`](MCP_SOURCE_REGISTRY.md)

This document does not define the earlier QA evidence-consumer **Track Q**.

## 0. Purpose

Implement a minimal, stable and safe **Product MCP** adapter layer over existing Genre_test capabilities so MCP-aware AI clients can use typed project capabilities without depending on internal PowerShell commands, Python entrypoints, temporary directories, console parsing or REAPER invocation details.

Primary principle:

> Product MCP does not replace Genre_test core, CLI, retrieval, QC, REAPER, Ozone or GitHub governance. Product MCP is an adapter over existing/stable service boundaries.

After implementation an AI consumer should primarily know **what** Genre_test can do rather than **how** its internals are wired.

### Relationship to QA Evidence Track

A separate early engineering track may consume read-only evidence through direct sources or MCP adapters.

Its dependency direction is:

```text
QA evidence collector
    -> Evidence Source abstraction
    -> direct/local/GitHub/MCP source
    -> ReviewEvidencePack
```

Track Q does **not** use or authorize:

```text
src/genre_test/mcp/**
```

and does not authorize the Product MCP server described by this document.

The canonical evidence contract must be transport-independent. An MCP server/client is not required merely to define or test `ReviewEvidencePackV1`.

Everything below in this document describing `src/genre_test/mcp/`, `get_project_status()`, `runtime_doctor()`, `analyze_audio()`, `get_qc_report()`, `compare_runs()` or other Genre_test server capabilities belongs to **Track P** unless explicitly amended by a later approved architecture task.

---

## 1. Preconditions before production implementation

Production Product MCP code must not start until all of these are true:

1. Track P remains a **v0.9 Product MCP task**. Starting Track Q earlier does not satisfy or bypass the Track P implementation preconditions.
2. Current MCP protocol revision is rechecked against [`MCP_SOURCE_REGISTRY.md`](MCP_SOURCE_REGISTRY.md).
3. Official Python SDK compatibility for the selected protocol revision is verified and a version/revision is selected for pinning.
4. Existing Genre_test service boundaries are inventoried and stable enough for the intended Product MCP surface.
5. No overlapping implementation Issue/branch/PR exists.
6. The implementation Issue defines exact allowed paths and acceptance criteria.

If the MCP specification is newer than `2026-07-28` at implementation time, do not silently use this document's protocol details as current truth. Reconcile the task against upstream first.

---

## 2. Non-goals

Do not:

1. Rewrite Genre_test around MCP.
2. Move domain/business logic into MCP handlers.
3. Create a second analysis/retrieval/QC/mastering backend.
4. Expose `run_shell(command)`, `exec(command)` or arbitrary PowerShell.
5. Expose unrestricted filesystem read/write.
6. Permit direct writes to `main` or force push.
7. Embed agent roles/orchestration logic inside the MCP server.
8. Make remote/cloud MCP mandatory for local use.
9. Change audio/DSP/retrieval/mastering semantics merely to fit MCP.
10. Break the existing human CLI/launcher workflow.
11. Treat early Track Q evidence work as authorization for Product MCP implementation.

---

## 3. Target architecture

```text
AI / Agent / MCP Host
          |
          v
     MCP Client
          |
          v
+--------------------------+
|   Genre_test MCP layer   |
|   thin typed adapter     |
+------------+-------------+
             |
             v
+--------------------------+
| Genre_test services/core |
| CLI adapters only where  |
| no stable service exists |
+-----+---------+----------+
      |         |
      v         v
 retrieval   analysis/QC
                  |
                  v
          REAPER/Ozone later
```

Dependency direction:

```text
MCP -> Genre_test service boundary -> core/backend
```

Never:

```text
core -> MCP-specific business logic
```

---

## 4. Protocol baseline requirements

Target the modern MCP model for the selected checked revision.

For `2026-07-28` specifically:

- requests are stateless/self-contained;
- protocol version and client capabilities are per-request metadata;
- do not design new core behavior around legacy protocol-level sessions;
- do not require legacy `initialize` as the modern architecture;
- implement/serve the required modern discovery behavior (`server/discover`) through the chosen official SDK/runtime;
- maintain compatibility behavior only when intentionally supported and tested.

Do not hand-roll JSON-RPC framing when the selected official SDK already implements the protocol correctly.

---

## 5. Phase 0 — discovery / architecture gate

Before MCP handlers are written, inventory stable project capabilities.

For each candidate operation record:

| Capability | Existing Python service? | CLI only? | PowerShell only? | Side effects | Stable enough? |
|---|---|---|---|---|---|
| Project status | | | | | |
| Runtime doctor | | | | | |
| Audio analysis | | | | | |
| Retrieval | | | | | |
| QC | | | | | |
| Run comparison | | | | | |
| Test execution | | | | | |
| REAPER render | | | | | |
| GitHub operations | | | | | |

Deliverable: architecture note/PR proving where the reusable service boundaries live.

Rules:

- prefer direct Python service calls over parsing human console output;
- if only CLI exists, consider extracting a reusable service before exposing it through MCP;
- do not duplicate a domain implementation merely to get an MCP endpoint quickly.

---

## 6. Recommended project structure

Exact placement is subject to Phase 0 findings. Preferred shape:

```text
src/genre_test/
  mcp/
    __init__.py
    server.py
    resources.py
    tools.py
    schemas.py
    errors.py
    policy.py

tests/mcp/
  test_server_discovery.py
  test_resources.py
  test_tools_readonly.py
  test_contracts.py
  test_errors.py
  test_security_boundaries.py

scripts/
  mcp_smoke.ps1

docs/
  MCP_ARCHITECTURE_PROPOSAL.md
  MCP_IMPLEMENTATION_TASK.md
  MCP_SOURCE_REGISTRY.md
  MCP_TOOL_CONTRACT.md        # create during implementation
  MCP_SECURITY.md             # create during implementation
```

Do not create a parallel second package if `src/genre_test/mcp` can stay a thin adapter.

---

## 7. MVP policy: read-only first

The first production-capable MCP milestone must be read-only from the repository/governance perspective.

It may execute bounded analysis/test operations that create normal derived run artifacts, but it must not modify repository code, merge PRs or expose generic system execution.

Read-only-first is a mandatory architecture gate before write-capabilities.

---

## 8. Server discovery

The selected implementation must expose correct modern capability/version discovery for the protocol revision it serves.

Acceptance:

- a compatible MCP client/Inspector can discover the server;
- reported protocol versions are accurate;
- advertised capabilities match implemented Tools/Resources/Prompts;
- server identity metadata is informational only and is not used as an authorization/security decision;
- compatibility with legacy clients is explicit, not accidental.

---

## 9. MVP Resources

Candidate resources:

```text
genre-test://project/active-current
genre-test://project/roadmap
genre-test://project/architecture
genre-test://project/source-registry
genre-test://project/version
genre-test://runtime/status
```

### Resource rules

1. Return canonical project information or explicit `NOT_AVAILABLE`/equivalent structured failure.
2. Never fabricate missing project state.
3. Do not expose arbitrary filesystem paths supplied by the caller.
4. Do not expose credentials, tokens, private keys, private corpora, local audio collections or unrelated user files.
5. Resource MIME/content types must match actual content.
6. Canonical project documents must be traceable to their repository path/version when practical.

Rejected generic resource/tool design:

```text
read_file(path="C:\\...")
```

If file access is ever required, define allowlisted project-scoped semantics instead.

---

## 10. MVP Tools

### 10.1 `get_project_status`

Purpose: return concise canonical project state.

Example output shape:

```json
{
  "project": "Genre_test",
  "version": "0.5.0.dev0",
  "default_branch": "main",
  "runtime_status": "ready"
}
```

Requirements:

- derive values from canonical sources where available;
- no hardcoded duplicate truth when a canonical source already exists;
- machine-readable output.

### 10.2 `runtime_doctor`

Purpose: check local runtime readiness using existing project diagnostics.

Example:

```json
{
  "status": "pass",
  "checks": [
    {"name": "python", "status": "pass"},
    {"name": "reaper", "status": "pass"}
  ]
}
```

Only check components actually required by the selected operation/profile.

### 10.3 `analyze_audio`

Purpose: run the standard Genre_test analysis pipeline.

Input concept:

```json
{
  "audio_path": "...",
  "profile": "default"
}
```

Requirements:

- validate file existence and supported type;
- enforce permitted path policy;
- prevent traversal/path escape;
- preserve source immutability;
- call existing analysis services;
- do not reimplement DSP/retrieval inside MCP;
- return a stable run/session identity.

Example output:

```json
{
  "run_id": "...",
  "status": "completed",
  "summary": {},
  "artifacts": []
}
```

### 10.4 `get_analysis_result`

Input:

```json
{"run_id": "..."}
```

Return the canonical stored/versioned result for that run.

### 10.5 `get_qc_report`

Return machine-readable QC for a run/session using existing QC semantics.

Do not reinterpret or invent thresholds in the MCP layer.

### 10.6 `compare_runs`

Input:

```json
{
  "left_run_id": "...",
  "right_run_id": "..."
}
```

Use existing comparison semantics. MCP must not add unreviewed heuristics.

### 10.7 `run_tests`

Purpose: execute only approved test suites.

Allowed interface pattern:

```json
{"suite": "default"}
```

or an allowlisted enum such as:

```text
default
mcp-contract
smoke
```

Forbidden:

```text
run_tests(command="pytest whatever --arbitrary-shell...")
```

---

## 11. Prompts

Prompts are optional and not required for the MVP.

If later useful, they must:

- be explicit reusable templates;
- remain user-controlled;
- not silently encode authority escalation;
- not replace `AGENTS.md` or task contracts;
- not be required for ordinary Tool/Resource use.

Example future candidate only:

```text
review-analysis-run(run_id)
```

Do not add prompts merely to increase MCP feature count.

---

## 12. Write-capabilities phase

Write-capabilities require a separate Issue/PR after the read-only layer is stable.

Possible later narrow operations:

```text
create_work_session()
request_render(session_id)
create_work_branch(name)
write_session_metadata(...)
```

Repository/GitHub actions must preserve current governance and should not duplicate a safer existing GitHub integration layer without a reason.

Never expose:

```text
run_shell(command)
exec(command)
run_powershell(script)
write_any_file(path)
delete_any_file(path)
git_push(ref)
git_force_push(...)
update_main(...)
```

---

## 13. Permission model

Design permission classes even if the first local MVP uses only a subset:

```text
READ_ONLY
AUDIO_EXECUTION
REPO_WRITE
RELEASE
```

### READ_ONLY

May:

- read approved Resources;
- get project/runtime status;
- read run/QC/comparison results.

### AUDIO_EXECUTION

May additionally:

- start approved analysis;
- later start approved render/QC workflows.

### REPO_WRITE

Future only:

- create a work branch;
- modify explicitly allowed repository paths through normal branch workflow.

### RELEASE

Future only and governed by `AGENTS.md`:

- release-specific actions only after exact preconditions are proven.

MCP permission classes do not replace GitHub Rulesets or agent-role authority.

---

## 14. Input validation

Every Tool must have a strict schema.

Validate at minimum:

- required fields;
- types;
- enums;
- length/range limits;
- canonical paths;
- existence of run/session IDs;
- supported profiles/suites;
- supported extensions;
- operation-specific preconditions.

Do not silently coerce an invalid request into a different action.

---

## 15. Error contract

Use one stable project error model mapped appropriately to MCP/SDK error behavior.

Suggested domain codes:

```text
INVALID_ARGUMENT
NOT_FOUND
NOT_AVAILABLE
PERMISSION_DENIED
RUNTIME_NOT_READY
OPERATION_FAILED
TIMEOUT
CONFLICT
UNSUPPORTED
INTERNAL_ERROR
```

Example domain payload:

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

Do not expose stack traces, secrets or internal credentials as the external error contract.

---

## 16. Output contracts

External results should be:

- machine-readable;
- deterministic where the underlying operation is deterministic;
- versionable;
- contract-testable;
- independent of human console formatting.

Suggested project envelope where useful:

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "contract_version": "1"
  }
}
```

Do not introduce wrappers that fight the official MCP result schema; adapt this concept to the selected SDK/protocol structures.

---

## 17. Path and filesystem security

Required negative cases:

```text
..\..\secret
C:\Windows\...
UNC/network escape where not approved
symlink/junction escape where applicable
unsupported extension
path outside approved roots
```

Rules:

1. Normalize and resolve before authorization decisions.
2. Use explicit allowlisted roots/policies.
3. Treat source audio as immutable.
4. Derived artifacts go only to project-approved run/session locations.
5. Never expose a generic filesystem browser as a shortcut.

---

## 18. Authentication and authorization

### Local stdio MVP

A local stdio server may not need the full remote OAuth flow, depending on the Host/client environment. This must not be misrepresented as "MCP has no authorization concerns."

The Host/process/user boundary still determines what the local server can access.

### Future remote/protected MCP

If Genre_test later exposes MCP over a protected network transport, perform a separate security design using the current MCP authorization specification.

At minimum re-evaluate:

- OAuth authorization-server discovery;
- PKCE;
- token audience/resource binding;
- token storage;
- HTTPS requirements;
- confused-deputy risk;
- explicit prohibition on token passthrough.

Do not reuse an inbound MCP token as an upstream service token.

---

## 19. Logging

Log internally:

- request ID/correlation ID;
- tool/resource operation;
- start/end;
- duration;
- result status;
- error code;
- run/session ID when applicable.

Do not log:

- access tokens;
- passwords;
- private keys;
- recovery codes;
- unnecessary full user-file content.

For stdio, protocol messages belong on stdout and diagnostics/logging belong on stderr so logs do not corrupt the protocol channel.

---

## 20. Local-first runtime

Initial target environment:

```text
Windows 11
PowerShell 7.x
Genre_test Python runtime
REAPER 7 where operation requires it
Ozone 12 Advanced where operation requires it
```

Preferred first transport candidate: **stdio**, subject to Phase 0 compatibility confirmation.

Desired documented startup shape:

```powershell
python -m genre_test.mcp.server
```

The final entrypoint must follow the actual project packaging/launcher conventions and should not bypass the project's supported user entrypoint policy without explicit design approval.

---

## 21. Smoke test

Add a project smoke harness, likely:

```text
scripts/mcp_smoke.ps1
```

Minimum checks:

1. Import/server startup.
2. Modern server discovery/version/capabilities.
3. List/read approved Resources.
4. Invoke `get_project_status`.
5. Invoke `runtime_doctor`.
6. Validate one invalid input.
7. Confirm generic shell/execution Tool is absent.
8. Confirm arbitrary filesystem Tool is absent.
9. Exit `0` on PASS, non-zero on FAIL.

Use MCP Inspector CLI or official SDK test utilities where they improve protocol-level confidence.

---

## 22. Test strategy

### Contract tests

Verify:

- discovery/version behavior;
- Tool exists;
- Resource exists;
- schema is correct;
- output contract is correct;
- error contract is correct;
- capabilities match implementation.

### Security negative tests

At minimum:

```text
path traversal
absolute system path outside policy
unsupported audio extension
invalid run_id
missing runtime
unknown suite
arbitrary shell-like payload
attempted direct-main/repo-write operation
```

Expected result: safe rejection.

### Regression tests

For operations that adapt an existing direct service:

```text
direct internal call result
vs
MCP adapter result
```

must preserve the same domain semantics within the existing project's documented tolerance.

MCP must not change DSP/retrieval/QC meaning.

---

## 23. MCP Inspector validation

The official MCP Inspector should be included in the implementation validation plan where practical.

Use it to verify:

- server connectivity;
- discovery;
- Tools/Resources listing;
- valid calls;
- invalid calls;
- returned structured content/errors;
- transport behavior.

If Node/Inspector becomes a CI burden, keep Python contract tests primary and use Inspector as an explicit smoke/developer gate; document the decision.

---

## 24. CI requirements

MCP tests integrate into the existing repository CI rather than creating a competing CI system.

Ready criteria:

```text
existing tests = PASS
MCP contract tests = PASS
security negative tests = PASS
supported Python matrix = PASS
```

No MCP PR is READY-MTD with red or missing required exact-head CI.

---

## 25. Audio Science trigger

Documentation/skeleton work that does not alter audio semantics does not require Audio Science solely because MCP will later call audio functions.

`AUDIO_SCIENCE` becomes mandatory if an MCP change alters or reinterprets:

- DSP/audio-analysis semantics;
- QC measurement methodology;
- mastering assumptions;
- Ozone parameter/module-order meaning;
- REAPER/Ozone render/readback behavior;
- comparison methodology.

For a pure adapter, Audio Science should verify semantic equivalence when the adapter touches audio-result contracts, not redesign the protocol layer.

---

## 26. GitHub governance

MCP must not bypass:

```text
branch
 -> Pull Request
 -> CI
 -> exact-head independent QA
 -> READY-MTD
 -> squash merge
 -> post-merge verification
```

Rules:

1. Direct `main` writes remain prohibited.
2. Force push remains prohibited.
3. Server-side `Protect main` Ruleset is defense-in-depth, not a substitute for MCP policy.
4. A future MCP GitHub Tool must be narrower than arbitrary git/shell access.
5. `RELEASE_MANAGER` authority remains defined by `AGENTS.md`, not by whether an MCP Tool exists.

---

## 27. Documentation required during implementation

Create/maintain:

### `docs/MCP_TOOL_CONTRACT.md`

Recommended table:

| Tool/Resource | Input | Output | Side effects | Permission | Domain owner |
|---|---|---|---|---|---|

### `docs/MCP_SECURITY.md`

Must contain:

- threat model;
- transport boundary;
- filesystem policy;
- secret policy;
- permission model;
- prohibited generic tools;
- remote-auth policy if applicable;
- audit/logging expectations.

Update [`MCP_SOURCE_REGISTRY.md`](MCP_SOURCE_REGISTRY.md) when protocol/SDK evidence changes.

---

## 28. Suggested PR sequence

Avoid one giant implementation PR.

### PR 1 — service inventory / architecture contract

- inventory stable service boundaries;
- choose protocol revision + Python SDK version;
- choose local transport;
- finalize schemas/security plan;
- no production MCP surface yet.

### PR 2 — read-only MCP skeleton

- server bootstrap;
- modern discovery;
- Resources;
- `get_project_status`;
- `runtime_doctor`;
- base schemas/error model;
- tests.

### PR 3 — analysis/QC adapter

- `analyze_audio`;
- `get_analysis_result`;
- `get_qc_report`;
- `compare_runs` where service boundary is stable;
- semantic regression tests.

### PR 4 — hardening

- path policy;
- permissions;
- security-negative tests;
- logging;
- PowerShell smoke;
- Inspector validation;
- docs completion.

### PR 5+ — write capabilities

Only after separate approval and read-only evidence.

---

## 29. Architecture rejection criteria

`ARCHITECT` should reject a Product MCP implementation if:

1. MCP handlers duplicate core business logic.
2. Generic shell/PowerShell execution is exposed.
3. Unrestricted filesystem access is exposed.
4. MCP can directly update `main`.
5. MCP server embeds the seven agent roles as its orchestration model.
6. MCP becomes a second source of project truth.
7. The human CLI is broken without a migration decision.
8. External contract requires parsing human console prose.
9. Security-negative tests are absent.
10. The implementation assumes legacy `initialize`/session semantics as the new modern core despite targeting `2026-07-28`.
11. Product MCP roadmap placement was silently accelerated.
12. Early Track Q work is used as a substitute for Product MCP service-boundary readiness.

---

## 30. QA checklist

Independent `QA_REVIEWER` should verify at least:

```text
1. server startup
2. server/discovery/version behavior
3. Tools discovery
4. Resources discovery
5. valid Tool call
6. invalid argument
7. nonexistent run
8. path traversal
9. runtime missing
10. core semantic regression
11. no arbitrary shell
12. no unrestricted filesystem
13. no direct-main capability
14. deterministic error contract
15. stdio logs do not corrupt stdout protocol
```

---

## 31. Definition of Done — read-only Product MCP MVP

The Product MCP MVP is complete only when all applicable items are true:

- [ ] Product MCP remains authorized for its roadmap placement and stable-service preconditions are met.
- [ ] Selected protocol revision revalidated.
- [ ] Official Python SDK version/revision pinned.
- [ ] MCP server starts locally on supported Windows environment.
- [ ] Modern discovery/version behavior is correct.
- [ ] Documented single startup entrypoint exists.
- [ ] MCP remains a thin adapter.
- [ ] Canonical Resources are implemented.
- [ ] `get_project_status` implemented.
- [ ] `runtime_doctor` implemented.
- [ ] At least one real analysis capability is exposed through a stable service boundary.
- [ ] Analysis result retrieval is implemented.
- [ ] QC result retrieval is implemented when stable in core.
- [ ] Stable error contract exists.
- [ ] No arbitrary shell/PowerShell Tool exists.
- [ ] No unrestricted filesystem Tool exists.
- [ ] No direct-main capability exists.
- [ ] Unit/contract tests PASS.
- [ ] Security-negative tests PASS.
- [ ] Existing regression tests PASS.
- [ ] Supported Python CI matrix PASS.
- [ ] Independent exact-head QA PASS.
- [ ] Documentation/source registry current.
- [ ] Merge follows branch/PR/CI/READY-MTD policy.
- [ ] Post-merge CI/test state verified.

---

## 32. Definition of Done — future write phase

Write capabilities require all read-only criteria plus:

- [ ] separate explicit scope approval;
- [ ] narrow domain-specific operations only;
- [ ] permission classification;
- [ ] destructive/precondition tests;
- [ ] audit trail;
- [ ] no direct-main path;
- [ ] no force-push path;
- [ ] no partial unsafe state on failure;
- [ ] GitHub governance preserved;
- [ ] remote authorization re-reviewed if transport is networked/protected.

---

## 33. Final success criterion

Product MCP is architecturally successful if a new compatible AI client can connect to Genre_test and use approved capabilities without knowing:

- internal PowerShell commands;
- internal Python entrypoints;
- temporary output paths;
- console formatting;
- REAPER invocation details;
- internal run-directory layout.

At the same time, existing human workflows remain independently usable and MCP does not become a privileged bypass around Genre_test safety/governance.

## 34. Short assignment for a future Product MCP implementation agent

> Design and implement a minimal local-first **Product MCP / Track P** adapter over existing stable Genre_test capabilities when the v0.9/stable-service preconditions are met. Revalidate the current MCP specification and pin an official Python SDK version before coding. Begin with modern discovery plus read-only Resources and narrow typed Tools. Keep all business logic in reusable Genre_test services, not MCP handlers. Do not expose arbitrary shell, PowerShell, filesystem or direct-main operations. Add strict schemas, structured errors, security-negative tests, existing-pipeline regression tests and protocol smoke validation. Develop through focused PRs with exact-head CI/QA and preserve current Genre_test governance. Controlled write capabilities require a separate follow-up approval. Early Track Q evidence work does not authorize this Product MCP implementation.
