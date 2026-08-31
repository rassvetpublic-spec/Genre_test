# oeksound DSP benchmark references

Status: research reference / optional external DSP benchmark candidates
Issue: #129
Revalidated: 2026-08-31

## Boundary

Commercial oeksound plug-ins are not Genre_test dependencies and are not bundled. They may be used only as externally installed, version-recorded **reference processors** in controlled local experiments.

Every render made with an oeksound processor for this research lane has role `reference-only`. It must not be labeled or interpreted as a Genre_test `SAFE`, `PROBE`, repair winner, mastering winner, or graduated production route.

The purpose is to validate Genre_test diagnostics and ordinary-processing robustness. It is not to infer that a plug-in is required for repair/mastering and not to optimize audio for AI-detector evasion.

Official references rechecked on 2026-08-31:

- Spiff: `https://oeksound.com/plugins/spiff`
- soothe3: `https://oeksound.com/plugins/soothe3/`
- Bloom: `https://oeksound.com/plugins/bloom/`
- downloads/version availability: `https://oeksound.com/downloads/`

The vendor describes Spiff as an adaptive transient processor, soothe3 as a dynamic resonance suppressor and Bloom as an adaptive tone shaper. Those descriptions define candidate roles only; they are not project ground truth about measured output deltas.

## Research-ledger requirement

Spiff, soothe3 and Bloom are separate candidates in `docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json` because they behave independently and need separate lifecycle/blocker/watch state.

Their registry status is `BLOCKED` until an installed/licensed local instance is available and the experiment can satisfy the admissibility/replay rules below. A commercial/trial installation may be used locally when authorized, but no activation data, binary, preset package or license material belongs in Git.

## Candidate roles

### Spiff

Role: transient/sustain calibration and repair-reference processor.

Useful experiments:

- controlled attenuation of transient attack;
- controlled enhancement of transient attack;
- test whether Genre_test attack-to-sustain, onset and transient-retention metrics move consistently with the **independently established** treatment;
- compare controlled variants against weak/smeared transient fixtures;
- verify that sustain/body metrics remain meaningfully independent where independently labeled or calibrated evidence supports that interpretation.

Suggested reference fixture matrix:

```text
R0 ORIGINAL
S1 SPIFF_ATTACK_MINUS_REFERENCE_MILD
S2 SPIFF_ATTACK_MINUS_REFERENCE_STRONG
S3 SPIFF_ATTACK_PLUS_REFERENCE_MILD
S4 SPIFF_ATTACK_PLUS_REFERENCE_STRONG
```

`REFERENCE_MILD` / `REFERENCE_STRONG` describe experiment strength only. They do not map to project `SAFE` / `PROBE` semantics.

Relevant controls include kick, snare, cymbal, guitar/pick, bass onset and vocal consonants.

### soothe3

Role: de-harsh/reference suppression and damage-guard validation.

Useful experiments:

- reduce persistent metallic/harsh/sibilant spectral energy;
- verify that apparent artifact reduction does not silently destroy drum attack or vocal consonants;
- measure phase/stereo/mono consequences under stronger adaptive processing;
- evaluate whether Genre_test harshness markers and transient/stereo guards disagree in sensible ways.

Suggested reference fixture matrix:

```text
R0 ORIGINAL
H1 SOOTHE_REFERENCE_MILD
H2 SOOTHE_REFERENCE_STRONG
```

A reference render that reduces harshness but fails transient, mono or stereo retention remains evidence about metric trade-offs. It does not graduate into a production route merely because one artifact marker improves.

### Bloom

Role: realistic adaptive tonal/mastering transformation for robustness testing.

Useful experiments:

- alter spectral balance and band dynamics in a musically plausible processing path;
- measure drift in MAEST/AST/CLaMP/MERT/Origin streams under ordinary mastering-like changes;
- test whether analysis/provenance evidence remains stable without treating the processor as an evasion tool.

Suggested reference fixture matrix:

```text
R0 ORIGINAL
B1 BLOOM_REFERENCE_BALANCED
B2 BLOOM_REFERENCE_STRONG
```

## T/S calibration: hypotheses are not ground truth

Do **not** assume that a Spiff attack treatment implies zero sustain/body change. Spiff is adaptive, and realized output can depend on source density, spectral content, detection behavior, decay/recovery settings, host/render behavior and gain treatment.

The expected direction table is therefore only a hypothesis:

```text
                         ATTACK- hypothesis   ATTACK+ hypothesis
attack energy                   down                up
transient/sustain ratio          down                up
onset strength                   down                up
sustain/body energy              unknown             unknown
```

A Genre_test T/S metric must not validate itself. Ground-truth or reference labels used to judge the metric must be established independently of the exact T/S implementation under test.

### Route B — mandatory independent sensitivity calibration

Before Spiff can be used as a realistic adaptive reference for T/S sensitivity claims, construct a project-owned attack-only or otherwise analytically controlled fixture whose intended change is known independently of Spiff and independently of the Genre_test T/S metric being evaluated.

The calibration may use analytically constructed edits, human-annotated event windows with a predeclared estimator, or another independently specified measurement method whose algorithm is not the metric under test. The calibration procedure, estimator and expected direction/range must be fixed before evaluating the candidate metric.

Route B is mandatory for the initial sensitivity validation of a T/S metric family.

### Route A — measured adaptive processor delta

After independent sensitivity calibration exists, a Spiff render may provide realistic adaptive evidence:

```text
source
  -> exact recorded Spiff treatment
  -> sample-align source and render with the predeclared alignment policy
  -> apply/log the predeclared metric-domain gain compensation
  -> compute aligned output and residual
  -> label realized attack and sustain/body deltas with the predeclared independent estimator/reference
  -> evaluate Genre_test T/S metrics against those independent labels
```

The estimator/reference used to label realized deltas must be independent of the exact Genre_test T/S metric being evaluated. Reusing the candidate metric's own output as its ground truth is prohibited.

A vendor preset name, knob direction or subjective expectation is not sufficient ground truth.

## Pairwise-analysis admissibility

Before the processor render is generated or its result is inspected, the experiment contract must lock:

1. the alignment estimator/method;
2. the allowed alignment search window or offset bounds and the rule for selecting the final offset;
3. the metric-domain gain-normalization basis and domain, including the exact window/band/channel basis when applicable;
4. the analysis windows used by the compared metrics, or the deterministic rule that derives them from immutable source annotations;
5. the listening-copy loudness-match method independently of the metric-domain gain policy.

Those policies must not be selected, widened, or replaced after inspecting the processed render in order to improve residual, T/S, spectral, mono/stereo or robustness results.

After rendering, an admissible pair must satisfy all of the following:

1. source and processed render are aligned using the predeclared method and bounds;
2. the realized latency/offset correction is recorded;
3. metric-domain gain compensation uses the predeclared basis and its realized value is logged so global level change cannot masquerade as a spectral/T/S improvement;
4. alignment and gain compensation are applied consistently to the predeclared analysis windows;
5. listening evaluation uses **separate loudness-matched copies** so perceptual preference is not biased by level;
6. raw immutable source and original processed render hashes remain preserved alongside any aligned/gain-compensated analysis copies.

If the predeclared alignment/gain policy cannot be applied, or if alignment or required gain compensation cannot be established inside its declared bounds, the pair is `NOT_ADMISSIBLE_COMPARISON`. A post-hoc alternate policy may be explored only as a new experiment with a new predeclared contract; it cannot rescue the original result.

## AI-origin / provenance robustness concept

For known-provenance sources, ordinary processing derivatives may be used to measure verdict/score drift:

```text
source
  -> EQ / compression / limiting / codec / resampling
  -> Spiff / soothe3 / Bloom reference variants
  -> OriginProfile evaluation
```

Before an origin/provenance robustness experiment, predeclare:

- the transformation family and permitted strength envelope;
- content-retention/admissibility bounds appropriate to that transformation;
- baseline-score uncertainty or repeated-measurement variability where measurable;
- the score-drift and/or verdict-change threshold that counts as a robustness failure;
- exclusions for near-threshold baseline cases where a categorical flip is expected from ordinary uncertainty.

A verdict flip or score shift outside those predeclared bounds is evidence of a candidate detector/benchmark robustness defect. A flip observed without those controls, near a decision threshold, or after a transformation that exceeds the prequalified ordinary-processing/content-retention envelope is only an observation requiring investigation; it is not automatically classified as a defect.

Forbidden interpretation:

```text
processing caused AI -> HUMAN
therefore processing is successful
```

Correct interpretation:

```text
processing changed origin evidence
therefore compare the change with predeclared robustness/uncertainty bounds
and investigate only the out-of-bound case as a candidate robustness defect
```

No oeksound treatment may be tuned toward detector-score reduction as an objective.

## Reproducibility requirements for adaptive processors

A saved plug-in state alone is insufficient evidence that an adaptive render is reproducible.

Every external DSP reference render used in a benchmark must record:

- plug-in name and exact installed version;
- host and host version;
- render mode, including offline/realtime and any quality/latency mode relevant to behavior;
- sample rate / bit depth / channel configuration;
- complete processor state: exported preset/full parameter state when available, otherwise normalized/manual parameter values and automation state plus a human-readable capture where permitted;
- source SHA-256 and original derived-output SHA-256;
- predeclared sample-alignment method/search bounds and realized offset;
- predeclared metric-domain gain-compensation policy and realized value;
- listening-copy loudness-match policy/value;
- processing manifest with `candidate_role: reference-only`;
- optional `reference_strength` such as `mild`, `balanced`, or `strong`;
- whether the plug-in was available/licensed locally.

### Replay-equivalence gate

Replay equivalence is mandatory for **every adaptive-processor result that is allowed to graduate into metric validation or robustness evidence**. A one-off adaptive render may remain exploratory/reference-only, but it cannot support a graduated project claim.

Before the replay render is generated, the experiment contract must predeclare:

1. the comparison domain(s) used by the claim, for example sample residual, transient windows, spectral bands, mono/stereo metrics or other named measures;
2. the equivalence threshold for every comparison domain on which the result will rely;
3. the alignment and gain-normalization policy used for replay comparison;
4. whether bit-identical output is expected or a bounded metric equivalence is the justified criterion.

Then:

1. reconstruct the processor from the recorded state in the recorded render mode;
2. rerender the same immutable source;
3. align the replay with the original reference render using the predeclared policy;
4. compare the replay against the original reference render in **all predeclared claim-covering domains**;
5. record the predeclared thresholds and observed results in the evidence manifest.

Thresholds must not be selected or widened after inspecting the replay result. A generic aggregate metric cannot substitute for a domain that materially supports the claim. If a T/S, stereo, spectral or other domain is used in the claim, replay equivalence must be bounded in that domain.

Until replay equivalence passes, the adaptive result is `NOT_ADMISSIBLE_REPRODUCIBILITY` and remains blocked/reference-only even if a preset/state capture exists.

Adaptive processing is not assumed bit-identical without evidence.

## Evidence roles

Keep these assets distinct:

```text
IMMUTABLE_SOURCE
ORIGINAL_REFERENCE_RENDER
ALIGNED_METRIC_COPY
GAIN_COMPENSATED_METRIC_COPY
LOUDNESS_MATCHED_LISTENING_COPY
REPLAY_RENDER
RESIDUAL / DELTA ANALYSIS
```

Derived comparison copies must retain parent hashes and processing metadata. They do not replace source truth.

## Graduation rules

An oeksound result may inform Genre_test metric validation only when:

- its registry entry is present and current;
- source and render identities are known;
- pairwise alignment/gain policy was predeclared before rendering/evaluation and admissibility passes within those bounds;
- listening copies are separately loudness matched;
- any T/S sensitivity claim has first passed an independent Route B calibration, and adaptive Route A labels are independent of the metric under test;
- adaptive replay equivalence passes against predeclared, claim-covering domains and thresholds;
- realized processor deltas are independently labeled/measured rather than assumed;
- any origin/provenance robustness claim uses predeclared transformation, content-retention and uncertainty/drift bounds;
- detector-score change is not used as processing success;
- Audio Science accepts the experiment design and interpretation.

Even then, the result validates or challenges a Genre_test metric/robustness hypothesis. It does not make the commercial processor a required project dependency.

## Related canonical docs

- `docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json`
- `docs/research/RESEARCH_OPERATING_RULES.md`
- `docs/GENERATIVE_AUDIO_TS_STEREO_DIAGNOSTICS_2026-08-28.md`
- `docs/GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`
- `docs/AI_ORIGIN_PROVENANCE_LAB.md`
- `docs/TECHNICAL_MASTERING_METRICS.md`
