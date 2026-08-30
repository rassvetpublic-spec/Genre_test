# Suno v5.5 mastering research — 2026-08-30

Status: **research hypotheses / not production defaults**
Issue: **#144**
Materialized in repository: **2026-08-31**

## Purpose

Preserve project-relevant findings from the 2026-08-30 Suno v5.5 / Ozone 12 research cycle without turning third-party observations into fixed mastering rules.

Canonical boundary remains:

```text
external source
-> bounded hypothesis
-> Genre_test project-owned measurement / A-B-X
-> only then candidate policy
```

Existing `docs/mastering/ozone12/core/16_SUNO55_LOSSY_SOURCE_TS_MASTERING_PROTOCOL.md`, repair diagnostics and backend-neutral mastering QC remain authoritative for current procedure. This file records additional evidence and benchmark hypotheses; it does not create a second mastering architecture.

## Evidence registry

### S1 — Suno v5.5 Remaster community regression report

Class: **COMMUNITY OBSERVATION**
Source: https://www.reddit.com/r/SunoAI/comments/1vnu1tv/community_alert_suno_v55_remaster_engine/

Reported in one direct community A/B:

- stronger HF harshness / sibilant or metallic texture;
- reduced low-mid warmth/body;
- flatter dynamics / stereo depth;
- phase-smear-like changes around attacks/tails.

Limitations:

- single/community evidence, not a Suno specification;
- does not establish prevalence across prompts, genres or source versions;
- must not justify fixed EQ cuts, width moves or automatic rejection.

Genre_test use: fixture discovery and regression hypothesis only.

### S2 — MasterForge Suno v5 vs v5.5 comparative measurements

Class: **THIRD-PARTY MEASUREMENT**
Source: https://masterforge.app/blog/suno-v5-vs-v5-5/

The source reports genre-dependent changes in spectral centroid, 2–5 kHz presence, sub-bass and stereo width across a small multi-genre comparison. Direction differs by genre rather than moving uniformly.

Limitations:

- small third-party sample;
- methodology/results are useful for hypothesis generation, not calibration truth;
- no aggregate percentage becomes a Genre_test threshold or model-wide rule.

Genre_test use: reinforces measured, genre/section-conditioned decisions instead of a universal v5.5 preset.

### S3 — iZotope Ozone workflow: Bass Control before Impact

Class: **VENDOR WORKFLOW REFERENCE**
Source: https://www.izotope.com/community/blog/10-steps-to-a-quick-master-in-ozone

Useful workflow idea: when both modules are needed, low-end balance/punch/sustain control can precede broader Impact microdynamic shaping.

Limitations:

- vendor workflow supports module capability/order testing, not Suno-specific defect prevalence;
- it does not establish universal settings or mandatory activation.

Genre_test use: benchmark the causal order `Bass Control -> Impact` under low-end/transient guards.

### S4 — Suno Band Manager Studio Editor reference

Class: **UPSTREAM / COMMUNITY REFERENCE**
Source: https://github.com/zarlor/suno-band-manager/blob/main/src/skills/_shared/references/STUDIO-EDITOR-REFERENCE.md

Useful secondary interpretation: Suno Remaster should be treated operationally as a new generative candidate/variant rather than assumed to be a deterministic EQ-style cleanup pass.

Limitations:

- secondary/community implementation reference;
- primary/vendor confirmation is preferred for exact product semantics;
- regardless of product internals, Genre_test evaluates the resulting audio as a separate derived candidate.

## Existing project context

Already-established sources/procedure include:

- Suno v5.5 release material;
- iZotope Ozone 12 product/workflow documentation;
- `TheApeMachine/deshimmer` transient-protection reference;
- `henricksmedia/shimmer` high-band / M-S cleanup reference;
- project-owned transient/sustain, mono/stereo and decoded-codec QC.

Do not reclassify those existing items as new findings merely because another source repeats them.

## H1 — Remaster is a separate candidate, not source truth

Benchmark independently:

```text
R0 = native/original Suno export
G1 = Suno v5.5 Remaster Subtle
D1 = DSP_SAFE candidate
O1 = OZONE_SAFE candidate
```

`G1` must pass the same project guards as any other derived candidate:

- loudness-matched comparison;
- event-aligned transient retention;
- HF instability/harshness inspection;
- low-mid/body comparison;
- Mid/Side, correlation and mono retention;
- codec audit where relevant;
- musical-damage listening gate.

A Remaster label never grants `SAFE` status.

## H2 — No universal Suno v5.5 mastering preset

Decision model:

```text
SOURCE MODEL + GENRE FAMILY + SECTION
        -> measured spectral / low-end / width / transient state
        -> eligible mastering candidates
```

Forbidden inference:

```text
v5.5 -> fixed presence cut
v5.5 -> fixed bass boost/cut
v5.5 -> fixed width percentage
v5.5 -> fixed LUFS/limiter drive
```

Third-party aggregate observations are not converted into fixed production parameters.

## H3 — Section-conditioned hybrid validation

For alternative-rock / dubstep / hybrid material, do not rely on one whole-track average when sections have materially different production states.

At minimum inspect representative regions for:

```text
ALT_ROCK
DUBSTEP
HYBRID_TRANSITION
TRANSIENT_RICH
SUSTAIN_OR_TAIL
```

Examples of independent questions:

- does the rock section lose snare/pick/front-edge attack?
- does the dubstep section carry excessive sub sustain into limiting?
- does the transition expose Side-only harshness or phase instability?
- does widening preserve kick/sub/vocal focus while widening intended sustain/tails?

This is a measurement/validation partition, not permission to invent semantic section labels without evidence.

## H4 — `Bass Control -> Impact` is a benchmark hypothesis

The experiment must change the target ordering while keeping downstream correction equivalent. Reference candidate A:

```text
repair / corrective stage
-> EQ / early Dynamic EQ as needed
-> Bass Control
-> Impact
-> Clarity / Stabilizer as needed
-> Imager
-> final Dynamic EQ / de-essing as needed
-> Maximizer
```

Ordering control B changes only the target pair when practical:

```text
repair / corrective stage
-> EQ / early Dynamic EQ as needed
-> Impact
-> Bass Control
-> Clarity / Stabilizer as needed
-> Imager
-> final Dynamic EQ / de-essing as needed
-> Maximizer
```

The post-Imager final Dynamic EQ/de-essing slot is bypassable but must exist identically in both comparison chains so widening-exposed Side harshness or imbalance is not confounded with the Bass Control/Impact ordering question.

Question to test:

> Does stabilizing low-end balance/punch/sustain before broader microdynamic shaping preserve attack and reduce limiter-driven drum loss better than the controlled alternative ordering?

Required comparison:

- same source and matched downstream loudness;
- target pair ordering is the only intended causal difference where practical;
- same bypass/activation state for all downstream modules in both candidates;
- transient attack-to-sustain retention;
- low-band peak/sustain behavior;
- mono/stereo guards;
- final limiter interaction;
- listening verdict.

`BYPASS` remains a valid winner for either module.

## Evidence policy

- Vendor documentation establishes capability/workflow, not Suno defect prevalence.
- Third-party measurements are supporting evidence until reproduced.
- Reddit/community reports are fixture-discovery/regression hypotheses only.
- No external claim promotes a candidate to `SAFE`.
- Project-owned aligned, loudness-matched measurement plus listening/A-B-X remains authoritative.
- Contradictory community reports are preserved as uncertainty, not averaged into a false consensus.

## Non-goals

This research does not authorize:

- an Ozone preset/XML/runtime change by itself;
- universal frequency cuts or boosts;
- universal width percentages;
- a universal LUFS/true-peak/limiter recipe;
- automatic ranking changes;
- edits to the frozen `rassvetpublic-spec/OZONE12_MASTERING_LAB` repository;
- detector-evasion or provenance-concealment optimization.

## Graduation

A hypothesis may affect production policy only after project-owned evidence demonstrates repeatable value on relevant fixtures and survives existing transient, mono/stereo, residual/damage and codec guards.
