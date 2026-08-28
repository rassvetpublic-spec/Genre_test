# Generative Audio Repair Benchmark — T/S + Stereo Addendum

Status: **design addendum**  
Base specification: `GENERATIVE_AUDIO_REPAIR_BENCHMARK.md`.

This addendum strengthens the existing transient/stereo measurements; it does not introduce mastering into the repair benchmark.

## Required source-role metadata

Add to every corpus item when known:

```text
source_role: LOSSLESS_SOURCE | LOSSY_SOURCE | UNKNOWN
codec
bitrate
sample_rate
observed_spectral_cutoff_hz
hf_confidence
```

For `LOSSY_SOURCE`, preserve the original immutable compressed file and decode once for deterministic analysis/candidate generation. No repeated intermediate lossy transcodes.

## Required transient/sustain measurements

In addition to existing crest and attack-to-sustain retention, report by relevant band and defect interval:

- event-aligned attack level;
- attack-to-sustain ratio;
- attack retention delta candidate vs original;
- onset density;
- transient-window spectral delta;
- sustain/tail-window spectral delta.

For de-harsh/de-shimmer routes, transient-retention is a **damage guard**. A candidate that reduces the target marker but removes legitimate drum/cymbal/consonant attacks must be rejected or sent to review.

## Required stereo measurements

Report globally, by band and around labeled intervals:

- Side/Mid ratio;
- inter-channel correlation;
- sample-aligned mono retention;
- transient-window correlation;
- sustain-window correlation;
- Side-specific versus Mid-specific harshness-marker change.

Do not convert width itself into a quality score. Wider and narrower candidates are judged by musical intent, mono survival and artifact/damage balance.

## New stress fixtures

Ensure pilot/calibration coverage includes:

1. drum-forward alt-rock / bass-music hybrids with strong kick/snare plus wide sustained textures;
2. deliberate stereo collapse/expansion transitions;
3. harshness mostly in Side content;
4. harshness mostly in transient content;
5. harshness mostly in sustain/tail content;
6. lossy-only MP3/AAC sources with clear codec cutoff;
7. clean controls containing intentional bitcrush/distortion/granular/vocoder texture so cleanup does not misclassify style as defect.

## Candidate comparison rule

For spectral cleanup candidates:

```text
artifact marker improves
AND event attack retention passes
AND mono/stereo retention passes
AND delta/removal does not contain excessive coherent music
AND loudness-matched blind review confirms lower artifact without unacceptable damage
```

No fixed `5–12 kHz`, Side amount or transient threshold is a benchmark constant. Such values remain backend settings to calibrate on pilot/calibration data and lock before test.

## Mastering separation

Ozone T/S imaging and module-chain choices may be evaluated later as robustness transformations, but they are **not repair backends inside this benchmark**. Genre_test reports measurements; OZONE12_MASTERING_LAB owns mastering-chain decisions.
