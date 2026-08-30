# ACTIVE / CURRENT

Published stable version: **none**  
Active development version: **0.5.0.dev0**  
Active milestone: **v0.5 CLaMP 3 semantic retrieval**  
Milestone epic: **#26**  
Long-term product epic: **#49 SUPERCOMBINE**
MCP adapter architecture proposal: **#146** (`REQUEST`; architecture/roadmap placement pending; no MCP implementation authorized by this status entry)

`Genre_test/main` plus current GitHub Issues/PR state is the canonical engineering source of truth. A fresh repository-aware agent should start with `docs/REPOSITORY_COLD_START.md` and must not depend on chat history for durable project state.

## Current execution state

There is deliberately no single hard-coded "current first implementation issue" in this file. GitHub Issues are task contracts and their live state changes faster than this summary.

For v0.5 execution, use:

1. open Issues under epic **#26** for live task state and acceptance criteria;
2. `docs/CLAMP3_TODO.md` for the current implementation/acceptance checklist;
3. the assigned Issue/PR for the exact next allowed action.

Known P0 state at this snapshot:

- **#27 runtime compatibility/isolation** — completed and merged via PR #72; selected architecture is an isolated persistent subprocess sidecar;
- **#28 retrieval schemas/protocol** — implementation foundation complete in main;
- **#29 real CLaMP 3 + MERT backend** — implementation and hardened target-PC evidence complete in main;
- **#30 persistent embedding cache/index** — implementation foundation is in main; real-catalog acceptance remains open;
- **#41 model licensing/provenance** — still open and remains a v0.5 release gate.

If no Issue is assigned, a new agent must not invent work from chat memory. It should inspect current open Issues and dependencies, then choose only a task that is unambiguously claimable under `AGENTS.md`.

## Product north star

Genre_test is evolving from a genre/profile analyzer into a local-first studio-finish workstation for generative songs:

```text
Generated mix / stems
  -> Analyze / Catalog / Search
  -> Technical QC + timestamped markers
  -> Repair artifacts
  -> Vocal/stem post-processing
  -> Mix/master orchestration
  -> Synchronized A/B/X review
  -> Metadata/tag audit
  -> Delivery / studio-ready master
```

The target is removal of audible defects, unstable synthetic artifacts and weak/raw production characteristics while preserving immutable sources, evidence provenance and reproducible processing manifests.

**AI-origin detector evasion, watermark stripping and provenance concealment are not product objectives.**

Planned long-term phases:

- v0.6 Repair & Stem Lab — #50, #51, #52; Apollo research is tracked under #63;
- v0.7 Studio Finish / mastering orchestration — including #54 comparison lab;
- v0.8 Metadata/Catalog/Delivery — #53, #56;
- v0.9 ComfyUI/runtime orchestration — #46, #55;
- v1.0 integrated SUPERCOMBINE.

See `ROADMAP.md` and `docs/SUPERCOMBINE_TODO.md`.

## Protected core analysis baseline

The protected ordinary-analysis baseline remains:

```text
Audio
  -> MAEST Discogs519 fine-style evidence
  -> AudioSet AST semantic evidence
  -> BPM / key / native source metadata
  -> deterministic profile fusion
  -> AudioProfile schema 4
  -> Normal / SUNO / Distributor views
  -> history / Validation / build comparison
```

Retrieval, repair and mastering work may not silently change these outputs without a dedicated reviewed migration.

Stable core runtime:

- **Python 3.13 x64 primary**;
- Python 3.12 x64 supported fallback;
- Python 3.11 unsupported;
- PyTorch 2.12.1;
- NVIDIA CUDA 13.0 / cu130;
- RTX 5070 Ti / `sm_120` proven on the target workstation;
- CPU-only mode supported;
- FFmpeg required for extended decode fallback.

The supported user entry point is `Genre_test_START.cmd`. Scripts under `scripts/` are implementation details unless a task contract says otherwise.

## Active v0.5: CLaMP 3 retrieval

Selected backend family: **CLaMP 3 SAAS + MERT + XLM-R** behind an **optional isolated persistent Python 3.12 subprocess sidecar**.

The isolated route was selected after real target-PC validation. The older upstream Python 3.10/CUDA 11.8 recipe is reference evidence only; core-native CLaMP inference was intentionally not selected.

Purpose:

- audio-to-audio semantic similarity;
- Russian/multilingual free-text-to-music search;
- representative segment search;
- custom segment search;
- persistent local catalog embeddings;
- deterministic Core Sound summary;
- later controlled zero-shot descriptors;
- conservative tempo/structure timeline after the segment foundation.

Planned GUI surface:

```text
Анализ | Каталог | Поиск | Validation | Проверка
```

CLaMP 3 does not replace MAEST, AudioSet AST, tempo/key DSP, AudioProfile, history, Validation or build comparison. Retrieval failure must not break ordinary Analyze startup.

Current-state retrieval contracts:

- `docs/CLAMP3_ARCHITECTURE.md`
- `docs/CLAMP3_RUNTIME.md`
- `docs/CLAMP3_RUNTIME_P0.md`
- `docs/CLAMP3_RETRIEVAL_ACCEPTANCE.md`
- `docs/THIRD_PARTY_MODELS.md`

Planning/scope references are useful for phase intent but are **not current-state authority**; if they conflict with `Genre_test/main`, live GitHub state, or the current-state contracts above, the current sources win:

- `docs/CLAMP3_ROADMAP.md`
- `docs/CLAMP3_TODO.md`
- `docs/CLAMP3_OUTPUT_SCOPE.md`

Current retrieval state layout is flat under `.genre_test/`:

```text
.genre_test/
  history.sqlite3
  retrieval.sqlite3
  logs/
  models/
  runtimes/clamp3/.venv/
  upstream/clamp3/
```

## Third-party model gate

CLaMP code/selected weight provenance is recorded, while the documented audio path uses `m-a-p/MERT-v1-95M`, whose model terms remain a release constraint tracked by **#41**.

Until that gate is complete:

- the MERT-backed retrieval backend remains optional/experimental for release-policy purposes;
- no MERT weights are committed or bundled;
- the stack is not described as commercially unrestricted;
- exact model revisions/checksums/licenses remain part of provenance diagnostics and release documentation.

## v0.5 output truth rule

```text
MEASURED / MODEL EVIDENCE
  -> RESOLVED ANALYSIS
  -> DETERMINISTIC DESCRIPTION
  -> OPTIONAL CREATIVE RECOMMENDATIONS (future)
```

Descriptions must never outrun their evidence. CLaMP similarity is not automatically a calibrated semantic fact, and structure change-points must not be promoted to Verse/Chorus/Drop labels without evidence.

## Large-catalog evidence

Existing v0.4 history provides the first real retrieval corpus:

```text
10,439 discovered files
10,436 successful Auto analyses
10,383 semantic OK
~775 h audio
```

This history should be reused as catalog metadata. Retrieval indexing must not unnecessarily rerun MAEST/AST.

## Geekatplay integration status

Existing forks:

```text
rassvetpublic-spec/music-suite
rassvetpublic-spec/ComfyUI-MusicMapper-nodes
```

`docs/GEEKATPLAY_ORG_AUDIT.md` is the canonical reuse audit. Selected directions include:

- Music Suite technical metrics/markers and mastering-orchestration patterns;
- Song Geometry Mapper time/feature/edge concepts;
- synchronized comparison ideas from ABCvers;
- asset integrity/provenance/lineage patterns;
- model-cache/runtime patterns for future shared GPU scheduling.

These are evidence/reuse inputs, not permission to copy code without per-upstream provenance and license checks.

## Retained analysis regression baseline (from retired v0.4 line)

These behaviors remain useful regression expectations even though the v0.4 release/tag/package line is retired:

- default output view: `all`
- optional full source path
- live Device / mode / view / path switching between tracks
- Safe Stop for Analysis and Validation
- dark theme by default with live Dark / Light switching
- Expert mode exposes MAEST windows and Top-K
- CPU-only UI does not offer CUDA
- History and log paths clickable

## Ozone 12 mastering consolidation

`Genre_test` is the only active engineering destination for AUDIO_MASTERING.

Ozone 12 Advanced is an optional v0.7 mastering backend and REAPER is its render host. The active Ozone knowledge/config/tooling boundary is:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

The standalone `OZONE12_MASTERING_LAB` repository and `legacy/OZONE12_MASTERING_LAB/` are frozen migration/provenance evidence. New mastering architecture and implementation belong in Genre_test.

Backend-neutral measurements belong in shared technical/QC layers; Ozone XML, ParamID/schema/build guards, `ElementChain`, preset construction and REAPER/Ozone render logic stay inside the Ozone boundary.

See `docs/mastering/ozone12/README.md` and `docs/mastering/ozone12/MIGRATION_FROM_OZONE12_MASTERING_LAB.md`.

## Release state

There is **no currently published packaged stable release**. The former v0.4 portable release line has been retired from the active repository and GitHub Releases/Tags.

`Genre_test_START.cmd` retains packaged-mode bootstrap capability for a future release, but no historical v0.4 ZIP or checksum file is an active release artifact or source of truth.

## Governance and merge policy

`AGENTS.md` is authoritative for repository governance.

Key current rule: the project has **standing automatic MTD authorization** for already approved-scope work. Once a PR reaches exact-head `READY-MTD <40-char-sha>` with all required QA, Audio Science when triggered, CI, scope and evidence gates satisfied, `RELEASE_MANAGER` may merge, verify `main`, and delete the merged head branch without requesting a fresh MTD token.

Standing MTD does **not** authorize new/material architecture decisions, scope expansion, unrelated work, missing/inconclusive evidence, or bypassing required review gates. Explicit `mtd`, `MTD` or `мтд` remains a valid scoped override.

## Repository governance

Canonical repository: `rassvetpublic-spec/Genre_test`.

Current governance baseline:

- repository visibility: **public**;
- default branch: `main`;
- GitHub Ruleset: `Protect main`, enforcement `active`, applies to the default branch;
- direct updates require a Pull Request;
- merge method allowed by the Ruleset: squash only;
- live required status contexts remain `test (3.11)`, `test (3.12)`, `test (3.13)` during the ruleset migration;
- `test (3.11)` is now a lightweight **retirement sentinel** that verifies Python 3.11 is rejected; it does not install or execute Python 3.11;
- `test (3.12)` runs compatibility pytest only;
- `test (3.13)` is the primary full quality/runtime-contract + pytest gate;
- docs-only PRs keep the required contexts, skip heavy Python setup/Ruff/full pytest, run lightweight repository contract tests on Python 3.13, and fail the required contexts if preflight fails;
- superseded PR CI is cancelled through workflow concurrency;
- merge-to-main no longer repeats the full matrix; it runs only a lightweight Python 3.13 merged-tree smoke;
- strict required-status-check policy is enabled;
- deletion and non-fast-forward updates are blocked;
- no Ruleset bypass actors are configured;
- the repository also retains `.githooks/pre-push` as a local defense-in-depth guard.

The legacy `test (3.11)` context name cannot be removed from the live GitHub ruleset through the currently available repository connector because that connector exposes ruleset reads but not administration writes. Removing that label is a governance migration only; it is no longer part of the supported runtime matrix.

Repository-owned governance configuration/check tooling lives under `config/github/`, `scripts/github-*.ps1`, and `CHECK_GOVERNANCE.cmd`.

## Cold-start acceptance

A fresh agent with only `Genre_test/main` and live GitHub state must be able to recover:

```text
PRODUCT
CURRENT VERSION
CURRENT MILESTONE
CURRENT ARCHITECTURE
PROTECTED BASELINES
COMPLETED WORK
ACTIVE / BLOCKED WORK
GOVERNANCE
ASSIGNED TASK CONTRACT
NEXT ALLOWED ACTION
```

The exact recovery procedure and conflict policy are defined in `docs/REPOSITORY_COLD_START.md`.
