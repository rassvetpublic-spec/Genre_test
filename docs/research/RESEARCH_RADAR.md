# Genre_test Research Radar v2

Status: **canonical periodic research procedure**

Research Radar is the recurring discovery layer for Genre_test. It does not replace
`RESEARCH_OPERATING_RULES.md`, agent governance, specialized registries, project
architecture, or roadmap authority.

## 1. Source-of-truth order

For a Radar run, load current `main` and read in this order:

1. `AGENTS.md`;
2. `docs/research/RESEARCH_OPERATING_RULES.md`;
3. this file;
4. `docs/research/data/RADAR_TOPICS.json`;
5. `docs/research/data/SOURCE_REGISTRY.json`;
6. `docs/research/data/RESEARCH_STATE.json`;
7. specialized registries and canonical documents referenced by the registry;
8. recent relevant evidence/run records.

Mutable Radar topics, registry index and run state are canonical in JSON.
Markdown under `docs/research/obsidian/` and
`docs/development/research_radar/` is a generated projection only.

If generated Markdown disagrees with canonical JSON, JSON wins and the projection
must be regenerated. Chat memory never wins over current repository state.

## 2. Discovery cycle

For every run:

1. resolve the requested time window and active topics;
2. inspect current state before searching so known work is not rediscovered as new;
3. prefer primary papers, official repositories, model cards, specifications,
   changelogs and vendor documentation;
4. use secondary/community material for discovery or hypothesis generation, not
   as proof by itself;
5. normalize each candidate to a stable identity (canonical URL/repository,
   paper identifier, model/checkpoint identity or equivalent);
6. deduplicate against the general registry index, specialized registries,
   current Issues/PRs and recent run evidence;
7. classify evidence separately from inference;
8. either register a useful candidate, update an existing candidate, record an
   explicit rejection/supersession reason, or preserve a concrete blocker;
9. for test-required findings, hand off an experiment or blocker under
   `RESEARCH_OPERATING_RULES.md`;
10. update state only for work actually performed;
11. regenerate Markdown projections;
12. run `python tools/research_radar_sync.py --check` before considering the
    repository state consistent.

## 3. Radar topics

`RADAR_TOPICS.json` defines recurring discovery domains, search keywords and
explicit exclusions. Topic entries are machine state and should stay compact.
A topic can be paused without deleting its history.

Adding a topic does not change product roadmap priority. Researcher suggestions
remain proposals until accepted through normal project governance.

## 4. Registry model

`SOURCE_REGISTRY.json` is a cross-domain index. It points to canonical project
documents or specialized registries and intentionally does not duplicate their
full technical content.

A specialized registry remains authoritative inside its domain. For example,
`AI_AUDIO_TOOL_TEST_REGISTRY.json` owns detailed lifecycle/test state for its
registered AI-audio tools.

## 5. Run state and evidence

`RESEARCH_STATE.json` records only durable machine state needed to continue the
next run. Initial/null values mean not run or not established; they must never
be filled from chat memory or guesswork.

Reproducible run evidence belongs in the project's designated research/run
evidence location. Do not commit raw search-result dumps, copied webpages,
temporary prompts, or unfiltered model output.

A concise run record should preserve:

- run identity/date and topic scope;
- search horizon and material upstream revisions when known;
- new/changed/rejected/blocked candidates;
- evidence class and primary-source identity;
- test/retest obligations created or cleared;
- state changes made;
- unresolved follow-up.

## 6. Obsidian projection

Run:

```text
python tools/research_radar_sync.py
```

to generate the Obsidian/Markdown projection.

The projection provides YAML frontmatter and `[[wikilinks]]` for graph
visualization. Generated metadata/body must not be edited as canonical state.
Obsidian-only human notes may be written only inside:

```text
<!-- MANUAL-NOTES-START -->
...
<!-- MANUAL-NOTES-END -->
```

The generator preserves that region.

Do not commit `.obsidian/` workspace settings as part of Radar state.

## 7. Compatibility facade

The historical paths under `docs/development/research_radar/` remain available
for older automation. They are generated compatibility views and redirect the
reader to this v2 system.

In particular, `RESEARCH_PROMPT.md` is no longer an independent giant prompt.
It is a stable bootstrap entrypoint that instructs an external Researcher to
load the canonical operating rules, Radar procedure and JSON state from current
`main`.

## 8. Completion rule

A Radar run is complete only when:

- durable findings are represented in canonical repository artifacts;
- newly discovered relevant candidates have not silently disappeared;
- required tests have either evidence or explicit blockers;
- state reflects only completed work;
- generated Markdown is synchronized with JSON;
- remaining uncertainty is explicit.

Deleting the originating chat must not remove a project-relevant source,
decision, test obligation, blocker or reproducible finding.
