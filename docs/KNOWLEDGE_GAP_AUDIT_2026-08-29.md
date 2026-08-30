# Knowledge Gap Audit — 2026-08-29

Issue: #129  
Scope: AUDIO_MASTERING / Genre_test durable engineering knowledge

## Verdict

The repository already contained the critical architecture and implementation knowledge for analysis/retrieval, generative repair, AI-origin research, Ozone 12 consolidation, shared mastering QC and agent governance.

A separate active task, **#126 / PR #128**, already owns repository cold-start consistency, including `docs/ACTIVE_CURRENT.md`, top-level architecture navigation and the repository-only recovery contract. Issue #129 therefore deliberately does **not** duplicate that work.

The remaining identified high-value gaps owned by #129 are bounded external research references that were discussed in AUDIO_MASTERING but not yet represented in `Genre_test/main`.

## Confirmed durable knowledge already present

- `AGENTS.md`: canonical authority/workflow/review/MTD and product boundaries.
- `docs/ACTIVE_CURRENT.md`: active implementation state and product north star; synchronization is owned by #126/#128.
- `ROADMAP.md` / `docs/SUPERCOMBINE_TODO.md`: staged product evolution.
- CLaMP3/MERT retrieval architecture and runtime contracts.
- GenerativeDefectProfile, repair benchmark and T/S + stereo diagnostics.
- AI Origin & Provenance multi-stream architecture, LOGO benchmark, robustness and uncertainty rules.
- Ozone 12 Universal Core v1.4.1 migration into the Genre_test namespace.
- shared transient/mono/stereo/decoded-codec mastering QC ownership.
- Ozone XML/ElementChain/build/schema executable ownership.
- legacy OZONE12_MASTERING_LAB boundary and preserved source snapshot.

## Universal Core v1.4.1 disposition check

The full `OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1.zip` snapshot is preserved in Git at:

```text
legacy/OZONE12_MASTERING_LAB/OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1.zip
```

The package SHA-256 recorded by the migration contract is:

```text
9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7
```

A direct archive inventory check on 2026-08-29 confirmed that the preserved package contains the complete v1.4.1 snapshot categories, including:

- core workflow/XML/T-S/module/Maximizer/codec/mastering-meter/Suno-lossy documents;
- profiles and decision/config tables;
- XML/T-S skills and parameter maps;
- stage/XML utilities;
- migration notes, templates and checklists;
- XML snippets;
- validation reports;
- the historical `source_consolidated/` and prompt material retained inside the snapshot.

Genre_test intentionally does **not** unpack every archived/duplicated file as active architecture. The active Ozone knowledge boundary is represented under `docs/mastering/ozone12/`, `config/mastering/ozone12/`, `tools/mastering/ozone12/` and `src/genre_test/mastering/ozone12/`; the preserved ZIP is the complete migration/provenance fallback. This distinction prevents archived duplicate material from competing with current `Genre_test/main` contracts while retaining the original knowledge snapshot in Git.

## Gaps identified and closed by #129

### External AI detector validation references

Previously discussed external services were not represented in `main`. Added:

`docs/research/EXTERNAL_AI_MUSIC_DETECTORS.md`

The document records entry points and, more importantly, the interpretation boundary: external detector scores are comparison evidence only, not ground truth and not mastering/repair optimization targets.

### oeksound benchmark/reference roles

The Spiff/Soothe3/Bloom research was not represented in `main`. Added:

`docs/research/OEKSOUND_BENCHMARK_REFERENCES.md`

The roles are constrained to controlled local benchmarking:

- Spiff: T/S calibration/reference perturbations;
- soothe3: de-harsh reference and transient/stereo/mono damage-guard testing;
- Bloom: realistic adaptive tonal/mastering robustness transform.

No commercial dependency or binary is introduced.

### Research index

Added:

`docs/research/README.md`

It marks these notes as bounded/date-sensitive external research rather than production truth.

## Cold-start dependency

Repository-only recovery and current-state synchronization are intentionally delegated to **#126 / PR #128**, which was already active when this audit was performed.

After #128 and #130 are both merged, the intended state is:

```text
#128 -> current-state / architecture / cold-start consistency
#130 -> missing external research knowledge
```

This avoids two competing implementations of `ACTIVE_CURRENT` or cold-start documentation.

## Deliberately not migrated

The following remain outside Git by design unless explicitly promoted later:

- private/user-owned audio;
- per-track renders and DAW sessions;
- local caches/history/logs;
- commercial plug-in binaries/licenses;
- API secrets;
- rejected or superseded brainstorms;
- conversational wording that does not change engineering decisions.

## Completeness criterion

For project continuation, `Genre_test/main` is considered knowledge-complete when a new repository-aware agent can determine, without old chats:

1. what the product is and what it is not;
2. current implementation priority versus long-term architecture;
3. subsystem ownership and boundaries;
4. accepted benchmark/evidence rules;
5. legacy provenance and migration status;
6. current Issue/PR workflow and next permitted action;
7. which external/local assets are optional and how they must be evidenced.

Issue #129 addresses only the missing research portion of that criterion. Issue #126/#128 addresses repository cold-start consistency. This does not imply literal archival duplication of every historical conversation.
