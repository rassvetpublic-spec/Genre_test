# Generative Audio T/S + Stereo Diagnostics

Status: **design / transferable diagnostics**  
Added: 2026-08-28  
Scope: `GenerativeDefectProfile`, Repair Lab and robustness measurements. This document does **not** define an AI-origin detector signal and does not define the Ozone mastering winner.

## 1. Boundary

The same audio properties can matter to mastering, repair and provenance research, but their roles must remain separate:

```text
Genre_test / Repair Lab:
  detect + localize + measure + damage-guard

OZONE12_MASTERING_LAB:
  decide whether/how to process the mastered delivery candidate

AI Origin & Provenance Lab:
  estimate origin/provenance from independent evidence
```

Do not optimize repair/mastering to reduce origin-detector evidence. Do not use this document for detector evasion, watermark removal or provenance concealment.

## 2. Source provenance and lossy confidence

Preferred analysis source is the highest-quality original available. When only MP3/AAC survives:

- preserve the immutable original and its hash;
- record codec, bitrate, sample rate and source role `LOSSY_SOURCE`;
- decode once to float PCM for deterministic analysis/repair comparisons;
- do not repeatedly transcode between candidates;
- estimate spectral cutoff/rolloff and lower confidence for high-frequency conclusions near/above it;
- never interpret a codec cutoff by itself as evidence of a generator or a particular defect.

A float decode is a processing container, not reconstruction of missing lossless information.

## 3. Transient/Sustain diagnostic axis

Add an explicit attack/body view in addition to ordinary spectrum/loudness metrics.

Recommended measurements per full track and per section/window:

- event-aligned peak/RMS attack level;
- pre-onset, attack and post-onset energy;
- attack-to-sustain ratio by band;
- onset density and event consistency;
- crest/PLR contextualized by event density;
- delta of these measurements between original and repair candidate.

Use at least low, low-mid, mid/presence and high bands. Exact crossover frequencies are analyzer configuration, not universal Suno thresholds.

### Damage guard

A de-harsh/de-shimmer/denoise candidate must not be promoted solely because an artifact marker decreases. Reject or review when the candidate removes legitimate:

- kick/snare front edge;
- cymbal attack needed for groove;
- vocal consonants;
- guitar/pick/percussive front edge;
- intentionally distorted broadband attacks.

When a backend exposes a removed/delta signal, inspect whether that delta contains coherent musical attacks rather than only defect residue.

## 4. Stereo diagnostic axis

Measure stereo globally **and by frequency band / section**:

- Mid and Side energy;
- Side/Mid ratio;
- inter-channel correlation;
- sample-aligned mono fold-down retention;
- transient-window correlation versus sustain/tail-window correlation;
- section-to-section width changes;
- left/right or M/S asymmetry of harshness markers.

A wide result is not automatically damage and a narrow result is not automatically safe. The question is whether important musical information survives mono and whether stereo behavior is stable relative to the intended source.

## 5. Generated-audio de-harsh / de-shimmer lessons

Community implementations such as `TheApeMachine/deshimmer` and `henricksmedia/shimmer` provide useful engineering hypotheses:

- protect transient/broadband musical events while reducing persistent spectral residue;
- allow Side and Mid evidence to differ instead of assuming identical cleanup strength;
- evaluate phase/stereo effects in addition to spectral reduction.

These are implementation ideas, not ground truth. Fixed community frequency bands or strengths must not become universal project thresholds.

Required flow:

```text
detect -> localize -> choose eligible route
-> Safe/Probe candidates
-> time alignment + loudness matching
-> artifact delta + transient guard + stereo/mono guard
-> controlled listening
```

## 6. Suno v5.5 evidence handling

Suno's own v5.5 release material describes richer arrangements, sharper vocals and more dynamic sound. Community reports additionally describe non-universal metallic/sibilant high-frequency texture, low-mid thinning, softened or flattened drum attacks and phase smear.

Project interpretation:

- vendor claims describe intended product behavior, not defect prevalence;
- community reports are fixture-discovery hypotheses;
- no single report justifies a universal `5–12 kHz` cut, LUFS target, width rule or detector feature;
- benchmark with real user-owned examples and clean controls before promoting thresholds.

## 7. Relationship to alternative-rock / dubstep material

Drum-forward hybrid material is especially useful for validation because it contains simultaneously:

- strong kick/snare transient requirements;
- sustained sub/bass body;
- distorted guitar/synth/vocoder/granular sustain;
- deliberate stereo expansion/collapse.

For diagnostics, explicitly compare whether a process changes **front edge** and **body/tail** differently. The mastering hypothesis `focused transient / wider sustain` belongs to OZONE12_MASTERING_LAB; Genre_test should only report measurements needed to judge whether such a candidate damaged attacks, mono or stereo stability.

## 8. Suggested GenerativeDefectProfile extensions

Add or reserve fields under a backward-compatible `extensions` namespace:

```text
source_role
source_codec
source_bitrate
observed_spectral_cutoff_hz
hf_confidence

transient_attack_db_by_band
transient_to_sustain_db_by_band
transient_retention_delta_db_by_band
onset_density

mid_side_ratio_db_by_band
correlation_by_band
transient_correlation_by_band
sustain_correlation_by_band
mono_retention_db_by_band
side_specific_harshness_markers
```

Thresholds remain calibration data, not schema constants.

## 9. Repair graduation additions

For generated-audio cleanup routes, graduation requires:

```text
artifact reduction demonstrated
AND legitimate transient retention passes
AND stereo/mono retention passes
AND clean controls are not over-processed
AND loudness-matched listening does not reveal musical damage
```

For lossy sources, report the codec lineage separately and avoid grading missing codec-removed air as a repair failure unless bandwidth restoration was explicitly the tested route.
