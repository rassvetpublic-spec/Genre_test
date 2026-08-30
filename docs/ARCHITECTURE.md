# ARCHITECTURE — current system map

Active development version: **0.5.0.dev0**

This file is the top-level architecture index for Genre_test. It intentionally does not duplicate every subsystem contract. A fresh agent should use this map to locate the authoritative document for the part of the system it is changing.

## Product boundary

Genre_test is a local-first Windows music analysis and studio-finish system for generative songs.

```text
Generated mix / stems
        |
        +--> Core Analysis / Profile --------------------------+
        |                                                      |
        +--> Retrieval / Catalog / Search ---------------------+
        |                                                      |
        +--> Technical QC / timestamped markers ---------------+
        |                                                      |
        +--> Repair / stem / vocal processing -----------------+--> derived candidates
        |                                                      |        |
        +--> Ozone/REAPER mastering orchestration -------------+        v
        |                                                           A/B/X review
        +--> Metadata / asset lineage / delivery --------------------+
                                                                    |
                                                                    v
                                                               studio-ready output
```

Protected existing analysis and active v0.5 retrieval must remain independently usable while later repair/mastering subsystems are developed.

## 1. Core Analysis / Profile — protected baseline

Ordinary analysis:

```text
file / folder input
      |
      +--> native source metadata --------------------------+
      +--> DSP: BPM / key / features ----------------------+ 
      +--> MAEST Discogs519 -------------------------------+--> AudioProfile fusion
      |      fine styles / broad families                  |        |
      +--> AudioSet AST -----------------------------------+        +--> Normal
             semantic genre/vocal/instrument/mood                   +--> SUNO
                                                                    +--> Distributor

raw MAEST evidence --> history / Validation / build comparison
```

Core modules include:

```text
profile_analyzer.py       ordinary MAEST + AST orchestration
analyzer.py               MAEST inference and mode-aware window cache
semantic_analyzer.py      pinned AudioSet AST inference
profile.py                AudioProfile evidence fusion / family reconciliation
analysis_policy.py        Auto/Fast/Accurate window selection
resolver.py               raw MAEST fine-style resolver
features.py               tempo/key/DSP features
source_metadata.py        original file metadata
presentation.py           Normal/SUNO/Distributor text views
```

Validation/history modules include content identity, append-oriented SQLite history, build identity, convergence and drift comparison.

Build identity is not analyzer semver alone. It includes the relevant combination of:

```text
analyzer_version
git_commit
schema_version
model_id
model_revision
```

Protected invariants:

- raw classifier/model evidence remains distinguishable from presentation labels;
- final Genre/Family output must be internally consistent;
- weak evidence must not be promoted into stronger certainty by normalization;
- `track_id` is content-based and survives moves/renames;
- history is append-oriented;
- Validation measures reproducibility/drift, not objective musical correctness;
- GUI and CLI share analysis logic;
- source audio is immutable.

## 2. Retrieval / Catalog / Search — active v0.5

Canonical documents:

- `docs/CLAMP3_ARCHITECTURE.md`
- `docs/CLAMP3_RUNTIME.md`
- `docs/CLAMP3_RUNTIME_P0.md`
- `docs/CLAMP3_TODO.md`
- `docs/CLAMP3_OUTPUT_SCOPE.md`
- `docs/CLAMP3_RETRIEVAL_ACCEPTANCE.md`

Selected architecture:

```text
Genre_test core
    |
    +--> versioned retrieval protocol
            |
            +--> persistent isolated Python 3.12 sidecar
                    |
                    +--> MERT audio frontend
                    +--> CLaMP 3 SAAS embedding space
                    +--> XLM-R multilingual text path
            |
            +--> retrieval.sqlite3
                    +--> versioned embedding identities
                    +--> exact cosine index
                    +--> query history
                    +--> segment / representative metadata
```

Retrieval is optional. `Retrieval: N/A/WARN/FAIL` may degrade retrieval features but must not make ordinary Analyze unusable.

CLaMP/MERT model identity, preprocessing and embedding identity are versioned. Old/stale vectors are retained as forensic/versioned records rather than silently interpreted as current vectors.

## 3. Shared Technical QC / marker layer

Backend-neutral audio measurements belong in shared Genre_test technical/QC code, not inside a mastering- or repair-specific duplicate implementation.

Examples:

- loudness / True Peak;
- clipping and timestamped problem regions;
- transient/drum-attack retention;
- stereo correlation / Mid-Side / mono-loss diagnostics;
- decoded codec peak checks;
- spectral/harshness/sibilance/sub-bass markers;
- before/after technical guards.

Primary planning references:

- `docs/SUPERCOMBINE_TODO.md`
- Issue #45 TechnicalProfile
- `docs/GEEKATPLAY_ORG_AUDIT.md`

Truth hierarchy:

```text
MEASURED / FILE METADATA / MODEL EVIDENCE
        -> RESOLVED ANALYSIS
        -> DETERMINISTIC DESCRIPTION
        -> OPTIONAL CREATIVE RECOMMENDATION
```

No layer may present an unsupported guess as measurement.

## 4. Repair / Stem / Vocal processing — planned v0.6

Canonical planning documents:

- `ROADMAP.md`
- `docs/SUPERCOMBINE_TODO.md`
- `docs/GENERATIVE_DEFECT_PROFILE.md`
- `docs/GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`
- `docs/GENERATIVE_AUDIO_REPAIR_SOURCE_REGISTRY.md`
- `docs/GENERATIVE_AUDIO_REPAIR_TOP10_AUDIT.md`

Target pattern:

```text
immutable source
  -> defect evidence / eligibility
  -> Original + Safe + Probe candidates
  -> bounded Refine
  -> before/after metrics + damage guard
  -> loudness-matched review
  -> winner / FULL_MIX_WINS / REGENERATE_SOURCE / INCONCLUSIVE
```

Every repair is a derived asset. Source identity, backend/checkpoint identity and processing provenance must remain recoverable.

## 5. Ozone 12 / REAPER mastering — planned v0.7

Canonical boundary:

```text
docs/mastering/ozone12/
config/mastering/ozone12/
tools/mastering/ozone12/
src/genre_test/mastering/ozone12/
```

Architecture:

```text
source audio
  -> Genre_test technical preflight
  -> versioned mastering request / candidate orchestration
  -> REAPER render host
  -> Ozone 12 Advanced
  -> derived WAV 24-bit / 48 kHz
  -> Genre_test shared technical QC
  -> A/B/X / delivery decision
```

Ozone 12 Advanced is an optional backend, not a dependency of normal analysis/retrieval startup.

Confirmed XML identity currently preserved in the integrated subsystem:

```text
PresetVer=6
PluginVer=120002
PluginBuild=1331
```

Ozone-specific ownership:

- XML schema and ParamID mapping;
- `ElementChain` encode/decode and exact module order;
- preset construction/patching;
- plugin version/build guards;
- REAPER/Ozone render/readback integration;
- Ozone-specific module policy.

Shared QC ownership:

- loudness/True Peak;
- transient retention;
- mono/stereo/Side-Mid diagnostics;
- codec preview/decoded peaks;
- before/after guards and derived-asset lineage.

Module order is semantically significant. The 16-slot map is a topology/order template, not a default command to enable every processor. `BYPASS` is a valid winner.

Canonical details: `docs/mastering/ozone12/README.md`.

## 6. Synchronized A/B/X review — planned v0.7

Issue #54 / `docs/SUPERCOMBINE_TODO.md` define the future comparison lab.

Architectural requirements:

- common transport and loop;
- 2–12 candidates;
- loudness-match;
- optional blind A/B/X;
- marker/waveform overlays;
- candidate processing manifests;
- technical summary and timestamp notes;
- selected-winner persistence;
- delta/null comparison where valid.

A/B/X is a decision layer; it must not silently alter source/candidate audio.

## 7. Metadata, asset lineage and delivery — planned v0.8

Primary work:

- metadata/tag audit and reversible writes (#53);
- local source/stem/render asset vault and lineage (#56);
- delivery package with canonical master, checksums, reports and processing provenance.

Identity metadata such as title/artist/album is not silently overwritten from model inference. File metadata, user-entered metadata and analyzer inference remain distinguishable.

## 8. Runtime / ComfyUI / automation — planned v0.9

Primary work:

- Genre_test-owned ComfyUI bridge nodes (#46);
- shared GPU `ModelRuntimeManager` / VRAM scheduler (#55);
- stable local job API with progress, heartbeat and Safe Stop;
- optional MCP facade only after stable local contracts exist.

Heavy models must have explicit acquire/release lifetime, observable resource usage and bounded failure behavior. Optional backends fail independently.

## 9. Agent governance and repository workflow

Canonical governance:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `docs/AGENT_WORKFLOW.md`
- current GitHub Issue/PR state

Roles are deliberately separated: REPO_STEWARD, RESEARCHER, ARCHITECT, CODER, QA_REVIEWER, AUDIO_SCIENCE and RELEASE_MANAGER.

No direct commits to `main`. GitHub Issues are task contracts. QA/Audio Science/READY-MTD evidence is exact-head scoped. The project currently has standing automatic MTD for approved-scope PRs that reach exact-head readiness; that authority does not cover new/material decisions or missing evidence.

A new agent must recover context from repository/GitHub state, not from chat memory. See `docs/REPOSITORY_COLD_START.md`.

## 10. Runtime and persistence boundaries

Working-copy entry point:

```text
Genre_test_START.cmd
  -> project .venv / runtime checks
  -> Runtime Health
  -> GUI / retrieval subcommands
```

Current supported core runtime:

- Python 3.12–3.13, with 3.13 as the primary/default runtime and 3.12 as the supported fallback;
- PyTorch 2.12.1;
- CUDA 13.0/cu130 on supported NVIDIA hardware;
- CPU route supported;
- FFmpeg for extended decode fallback.

Local runtime state belongs under `.genre_test/` and is gitignored. Current key files/dirs include:

```text
.genre_test/history.sqlite3
.genre_test/retrieval.sqlite3
.genre_test/logs/
.genre_test/models/
.genre_test/runtimes/
.genre_test/upstream/
```

No private corpora, user audio, model weights, caches, virtual environments or session renders belong in Git unless intentionally reviewed as a fixture.

## 11. Source-of-truth precedence

When documents disagree, use this order:

1. `AGENTS.md` for governance and authority;
2. current GitHub Issue/PR/branch state for live task/workflow state;
3. `docs/ACTIVE_CURRENT.md` for current product/milestone summary;
4. this file for top-level architecture ownership and navigation;
5. subsystem architecture/contracts for the affected paths;
6. `ROADMAP.md` / TODO documents for future-phase context;
7. legacy/frozen material only as historical/provenance evidence.

Any unresolved contradiction is a stop condition. Report it instead of guessing.
