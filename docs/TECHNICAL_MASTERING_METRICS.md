# Technical mastering comparison metrics

Issue: #101  
Related TechnicalProfile work: #45

This module promotes the objective comparison logic that was previously owned
by `OZONE12_MASTERING_LAB/tools/stage_toolkit/oz12_mastering_meter.py` into a
backend-neutral Genre_test implementation.

## Ownership

Canonical implementation:

```text
src/genre_test/technical/mastering_metrics.py
```

CLI:

```text
genre-test-mastering-qc
```

Ozone, repair, stem processing, A/B/X review and future mastering backends must
reuse this implementation rather than carrying private copies of the same
measurement code.

The module is independent from MAEST, AST and CLaMP genre/retrieval evidence.
It does not mutate `AudioProfile` and is intended to feed the future
`TechnicalProfileOutputV1` contract from #45.

## Current identity

```text
schema: MasteringComparisonMetricsV1
algorithm_id: genre_test.technical.mastering_metrics:v1
```

Any material algorithm change requires a new algorithm identity.

## Transient retention

The detector finds strong broad-band onsets in the full stereo master. It is a
proxy, not drum-stem separation. After source/candidate alignment and active-RMS
matching it measures attack and attack-to-sustain deltas. Negative delta means
less event attack was retained. Thresholds are review policy, not universal
claims about musical quality.

## Mono retention / mono loss

Mono retention is defined as:

```text
10 * log10(power((L+R)/2) / mean(power(L), power(R)))
```

`0 dB` is a fully coherent centre signal. More negative values mean less energy
survives mono fold-down. Candidate-minus-reference is measured overall and by
frequency band. A negative delta means the derived candidate added cancellation
relative to its source.

## Decoded codec peak audit

Codec preview is optional and requires FFmpeg. Profiles are `mp3_320`,
`aac_256`, and `aac_192`. The audit performs a real encode -> float-WAV decode
-> FFmpeg `ebur128=peak=true` measurement. A trim recommendation is emitted only
when a target dBTP is supplied and must be rechecked after rerender.

## CLI

```powershell
genre-test-mastering-qc source.wav candidate.wav --output report.json
```

```powershell
genre-test-mastering-qc source.wav candidate.wav `
  --codec mp3_320 --codec aac_256 `
  --target-dbtp -1.0 `
  --output report.json
```

Exit code `2` means a configured hard guard failed. Warnings remain review
signals rather than automatic artistic rejection.

## Provenance

First implementation source:

```text
rassvetpublic-spec/OZONE12_MASTERING_LAB
a231b1af2cdb597578d4ea3f2d8cb6df964b1619
tools/stage_toolkit/oz12_mastering_meter.py
```

The standalone repository is historical source evidence. New technical
comparison development belongs to Genre_test.

## Non-goals

- no claim that detected full-mix onsets are isolated drums;
- no subjective `punchy`, `wide`, or `professional` verdict from metrics alone;
- no AI-origin/provenance detector objective;
- no Ozone or REAPER dependency for ordinary analysis/retrieval startup.
