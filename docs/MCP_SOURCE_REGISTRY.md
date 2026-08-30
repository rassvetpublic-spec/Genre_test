# Model Context Protocol (MCP) — source registry

Checked: **2026-08-30**  
Project: `rassvetpublic-spec/Genre_test`  
Related task: **#146**  
Primary protocol revision used by the project documentation: **2026-07-28**

## Purpose

This registry records the primary evidence behind the Genre_test MCP architecture proposal and implementation task. It exists so future agents can recover the protocol assumptions from repository evidence instead of relying on chat memory.

The registry is not a vendored copy of MCP documentation. External protocol truth remains upstream; this file records which upstream pages were checked, what project conclusion they support, and how authoritative each source is.

## Evidence policy

Source classes:

- **CANONICAL** — normative MCP specification or schema for the checked revision.
- **OFFICIAL-GUIDE** — official MCP implementation/developer guidance.
- **OFFICIAL-RELEASE** — official release/change announcement useful for revision history.
- **BASE-STANDARD** — external standard directly referenced by MCP.
- **PROJECT-CONTRACT** — current Genre_test repository/GitHub source of truth.

Rules:

1. Protocol semantics must be taken from the versioned MCP specification, not an old blog post or remembered pre-2026 behavior.
2. If the MCP specification advances beyond `2026-07-28`, recheck this registry before implementation or compatibility claims.
3. SDK APIs are implementation details and may change independently of the protocol; pin an SDK version/revision during implementation.
4. Security claims must not be weakened merely because the first Genre_test server is local.
5. Project roadmap placement is governed by current `Genre_test/main` and the user, not by MCP upstream documentation.

## Primary MCP sources

| # | Source | Class | What it establishes for Genre_test |
|---:|---|---|---|
| 1 | [MCP Specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | CANONICAL | MCP is an open protocol for connecting LLM applications with external context/tools; JSON-RPC 2.0; Host/Client/Server terms; server primitives Tools/Resources/Prompts; modern core is stateless and per-request capability aware. |
| 2 | [Architecture](https://modelcontextprotocol.io/specification/2026-07-28/architecture) | CANONICAL | Host coordinates clients/security/context; each client communicates with one server; servers expose focused capabilities; servers should not see the whole conversation or other servers; capability negotiation is per request. |
| 3 | [Versioning and Compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) | CANONICAL | `2026-07-28` is the modern stateless era: no negotiation handshake; every request declares protocol version; legacy `initialize` behavior belongs to `2025-11-25` and earlier compatibility. |
| 4 | [Key Changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) | CANONICAL | Removal of protocol-level sessions and `initialize`/`notifications/initialized`; addition of `server/discover`; modern per-request `_meta`; Multi Round-Trip Requests and other revision changes. |
| 5 | [Server Discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover) | CANONICAL | Modern servers MUST implement `server/discover`; it reports supported protocol versions, capabilities and identity; identity metadata is not a security signal. |
| 6 | [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) | CANONICAL | Tools are server-exposed executable functions, discovered/invoked through typed protocol contracts; tool use requires declared capability and must be treated as a security-sensitive action. |
| 7 | [Resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources) | CANONICAL | Resources expose context/data through URI-based contracts; supports discovery/read semantics and structured resource metadata. |
| 8 | [Prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts) | CANONICAL | Prompts are server-exposed reusable templates, designed to be user-controlled and explicitly selected; they are distinct from Tools and Resources. |
| 9 | [stdio transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio) | CANONICAL | Local client launches server as subprocess; JSON-RPC uses stdin/stdout; logs belong on stderr; protocol is stateless; modern/legacy probing behavior is defined. |
| 10 | [Authorization Security Considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations) | CANONICAL | Authorization/token audience, secure token storage, PKCE, HTTPS/localhost redirect rules, confused-deputy and token-passthrough protections for protected/remote MCP deployments. |
| 11 | [Official SDK list](https://modelcontextprotocol.io/docs/2026-07-28/sdk) | OFFICIAL-GUIDE | Python is a Tier 1 official SDK; official SDKs cover servers, clients, local/remote transports and typed protocol support. Does not by itself choose the Genre_test implementation version. |
| 12 | [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector) | OFFICIAL-GUIDE | Reference developer tool for testing/debugging MCP servers; web/CLI/TUI clients can be used in smoke and contract testing. |
| 13 | [2026-07-28 specification release](https://blog.modelcontextprotocol.io/posts/2026-07-28/) | OFFICIAL-RELEASE | Release provenance for revision `2026-07-28`; summarizes stateless core, discovery, authorization hardening and other changes. |
| 14 | [Official MCP specification repository](https://github.com/modelcontextprotocol/modelcontextprotocol) | CANONICAL | Upstream source repository for versioned specification/schema and change history. |
| 15 | [Official Python SDK](https://github.com/modelcontextprotocol/python-sdk) | OFFICIAL-GUIDE | Candidate implementation library for Genre_test because Genre_test is Python-first; exact SDK version/API must be selected and pinned during an implementation spike. |

## Base standards

| # | Source | Class | Project relevance |
|---:|---|---|---|
| 16 | [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) | BASE-STANDARD | MCP uses JSON-RPC 2.0 message semantics. Genre_test should normally rely on the official MCP SDK rather than hand-roll wire protocol handling. |
| 17 | [RFC 8707 — Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707) | BASE-STANDARD | Referenced by MCP authorization requirements for token audience/resource binding. Relevant if/when Genre_test exposes a protected remote MCP server. |
| 18 | [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728) | BASE-STANDARD | Used by MCP authorization-server discovery for protected resources. Not required for a simple local stdio MVP, but required evidence for future remote auth design. |

## Project-local sources

| # | Source | Class | Project authority |
|---:|---|---|---|
| 19 | [`AGENTS.md`](../AGENTS.md) | PROJECT-CONTRACT | Agent roles, exact-head QA, branch/PR/CI/READY-MTD workflow, authority boundaries and standing automatic MTD. MCP cannot bypass these rules. |
| 20 | [`docs/ACTIVE_CURRENT.md`](ACTIVE_CURRENT.md) | PROJECT-CONTRACT | Current project state and explicit MCP proposal pointer. |
| 21 | [`ROADMAP.md`](../ROADMAP.md) | PROJECT-CONTRACT | Current roadmap places an optional MCP façade in v0.9 after stable local APIs exist. This remains authoritative until the user approves a priority change. |
| 22 | [Issue #146](https://github.com/rassvetpublic-spec/Genre_test/issues/146) | PROJECT-CONTRACT | Active MCP architecture/documentation task and unresolved roadmap-placement decision. |

## Consolidated protocol facts used by the project

The following facts are considered verified for the checked `2026-07-28` revision:

1. MCP is a protocol/interface layer, not an AI agent and not the Genre_test backend.
2. The architecture is Host -> Client -> Server; one host can manage multiple clients, and each client has a 1:1 relationship with a server.
3. Server primitives include **Tools**, **Resources**, and **Prompts**.
4. Modern MCP requests are stateless/self-contained and carry protocol version/capabilities per request.
5. `server/discover` is the modern capability/version discovery method servers must implement.
6. `initialize`/session-based assumptions belong to legacy compatibility and must not be designed as the new Genre_test core contract.
7. stdio is a canonical local transport and is therefore a strong candidate for Genre_test's first local Windows implementation, but the architecture decision is not final until the implementation issue explicitly selects it.
8. Tools are security-sensitive. A generic arbitrary-shell tool would defeat the intended narrow typed boundary and is rejected by the Genre_test design.
9. Remote/protected MCP authorization has non-trivial OAuth/security requirements; remote deployment is therefore not part of the read-only local MVP unless separately approved.
10. Official Python SDK and MCP Inspector are appropriate implementation/testing candidates, but their exact versions must be pinned when implementation starts.

## Freshness / revalidation triggers

Recheck the registry when any of the following happens:

- MCP publishes a protocol revision newer than `2026-07-28` and Genre_test implementation is about to start or upgrade;
- official Python SDK support for the selected protocol revision changes materially;
- Genre_test moves from local stdio to remote/network MCP;
- new write-capabilities are proposed;
- MCP authorization/security requirements change;
- the roadmap moves MCP earlier than v0.9.

## Explicit non-sources

The following are not protocol sources of truth:

- chat memory;
- generic MCP tutorials copied without revision/version context;
- old examples that assume `initialize`/session semantics without a compatibility label;
- model-generated summaries when they conflict with the versioned official specification.
