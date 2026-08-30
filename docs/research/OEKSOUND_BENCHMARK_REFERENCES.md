# oeksound DSP benchmark references

Status: research reference / optional external DSP benchmark candidates  
Issue: #129  
Recorded: 2026-08-29

## Boundary

Commercial oeksound plug-ins are not Genre_test dependencies and are not bundled. They may be used only as externally installed, version-recorded **reference processors** in controlled local experiments.

Every render made with an oeksound processor for this research lane has role `reference-only`. It must not be labeled or interpreted as a Genre_test `SAFE`, `PROBE`, repair winner, mastering winner, or graduated production route.

The purpose is to validate Genre_test diagnostics and robustness, not to infer that a plug-in is required for repair/mastering and not to optimize audio for AI-detector evasion.

Official download/reference entry point: https://oeksound.com/downloads/

## Candidate roles

### Spiff

Role: transient/sustain calibration and repair-reference processor.

Useful experiments:

- controlled attenuation of transient attack;
- controlled enhancement of transient attack;
- check whether Genre_test attack-to-sustain, onset and transient-retention metrics move in the expected direction;
- compare controlled Spiff variants against weak/smeared transient SUNO fixtures;
- confirm that sustain/body measurements do not falsely track every transient-only change.

Suggested reference fixture matrix:

```text
R0 ORIGINAL
S1 SPIFF_ATTACK_MINUS_REFERENCE_MILD
S2 SPIFF_ATTACK_MINUS_REFERENCE_STRONG
S3 SPIFF_ATTACK_PLUS_REFERENCE_MILD
S4 SPIFF_ATTACK_PLUS_REFERENCE_STRONG
```

`REFERENCE_MILD` / `REFERENCE_STRONG` describe only uncalibrated experiment strength. They do not map to project `SAFE` / `PROBE` semantics.

Relevant musical controls include kick, snare, cymbal, guitar/pick, bass onset and vocal consonants.

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

A reference render that reduces harshness but fails transient, mono or stereo retention remains evidence about metric trade-offs; it does not graduate into a production route merely because one artifact marker improved.

### Bloom

Role: realistic adaptive tonal/mastering transformation for robustness testing.

Useful experiments:

- alter spectral balance and band dynamics in a musically plausible processing path;
- measure drift in MAEST/AST/CLaMP/MERT/Origin streams under ordinary mastering-like changes;
- test whether AI-origin evidence remains stable without treating the processor as an evasion tool.

Suggested reference fixture matrix:

```text
R0 ORIGINAL
B1 BLOOM_REFERENCE_BALANCED
B2 BLOOM_REFERENCE_STRONG
```

## T/S ground-truth calibration concept

For controlled local fixtures, Genre_test should observe expected directional changes:

```text
                         ORIGINAL   ATTACK-    ATTACK+
attack energy               0         down       up
transient/sustain ratio      0         down       up
onset strength               0         down       up
sustain/body energy          0       approx 0   approx 0
```

Exact numeric thresholds must come from calibration data, not from a plug-in preset or vendor recommendation.

## AI-origin robustness concept

For known-provenance sources, ordinary processing derivatives may be used to measure verdict/score drift:

```text
source
  -> EQ / compression / limiting / codec / resampling
  -> Spiff / soothe3 / Bloom reference variants
  -> OriginProfile evaluation
```

Desired property: ordinary production processing should not cause uncontrolled origin-score or attribution flips. If it does, that is a detector robustness defect to investigate.

Forbidden interpretation:

```text
processing caused AI -> HUMAN
therefore processing is successful
```

Correct interpretation:

```text
processing caused unstable origin evidence
therefore the detector/benchmark needs robustness work
```

## Reproducibility requirements

Every external DSP reference render used in a benchmark must record:

- plug-in name and exact installed version;
- host and host version;
- sample rate / bit depth / channel configuration;
- complete parameter/preset identity when reproducibly exportable;
- source SHA-256 and derived-output SHA-256;
- loudness/alignment treatment;
- processing manifest with `candidate_role: reference-only`;
- optional separate `reference_strength` such as `mild`, `balanced`, or `strong` when useful for the experiment;
- whether the plug-in was available/licensed locally.

`candidate_role` must remain `reference-only` for every oeksound render in this research lane. `SAFE` and `PROBE` are reserved for project candidate semantics and must not be used here.

No commercial binary, license material or user-specific activation data belongs in Git.

## Related canonical docs

- `docs/GENERATIVE_AUDIO_TS_STEREO_DIAGNOSTICS_2026-08-28.md`
- `docs/GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`
- `docs/AI_ORIGIN_PROVENANCE_LAB.md`
- `docs/TECHNICAL_MASTERING_METRICS.md`
