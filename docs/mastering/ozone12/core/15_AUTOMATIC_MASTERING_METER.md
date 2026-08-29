# 15. Backend-neutral Mastering QC

The standalone `tools/stage_toolkit/oz12_mastering_meter.py` implementation is
retired. The canonical active implementation is shared by repair, mastering,
codec preview and future A/B/X workflows:

```text
src/genre_test/technical/mastering_metrics.py
CLI: genre-test-mastering-qc
schema: MasteringComparisonMetricsV1
algorithm_id: genre_test.technical.mastering_metrics:v1
```

Do not restore or invoke the legacy meter as a second Ozone-specific
implementation. See `docs/TECHNICAL_MASTERING_METRICS.md` for the canonical
contract.

The active QC compares a reference/base WAV with a derived candidate using:

```text
broad-band transient-retention proxy
mono retention/loss relative to the reference
optional decoded MP3/AAC peak audit after real encode -> decode
```

These measurements do not modify audio and do not choose the musical winner.
Full-mix onsets are a proxy and are not drum-stem separation. Warnings and
failures remain technical evidence that must be interpreted with
loudness-matched listening.

## Requirements

```text
installed Genre_test environment
NumPy
SciPy
FFmpeg for codec audit
```

Inputs are PCM/float WAV files.

## Quick stage check

```powershell
genre-test-mastering-qc "BASE.wav" "CANDIDATE.wav" `
  --output "reports/mastering_qc.json"
```

## Final check with decoded codecs

```powershell
genre-test-mastering-qc "PRE_MAX_BASE.wav" "NATIVE_FINAL.wav" `
  --codec mp3_320 `
  --codec aac_256 `
  --codec aac_192 `
  --target-dbtp -1.0 `
  --output "reports/final_qc.json"
```

`-1.0 dBTP` is only an example declared delivery target, not a universal
default. Without `--target-dbtp`, decoded peaks remain measured evidence and
are not judged against an invented ceiling.

## Output and exit codes

With `--output`, the CLI writes one complete JSON report. Without it, the same
JSON is printed to stdout.

```text
0 = report completed without overall FAIL
2 = configured hard guard returned overall FAIL
```

Warnings remain review signals rather than automatic artistic rejection.

## Transient-retention proxy

1. Reference and candidate are time-aligned within `--max-lag-seconds`.
2. Candidate receives analysis-only active-RMS matching; the audio file is not
   rewritten.
3. Strong broad-band onsets are detected in the full stereo reference.
4. The same events are compared for attack and attack-to-sustain retention.

Current CLI defaults are configurable policy:

```text
attack warning: -0.75 dB
attack failure: -1.5 dB
```

They are heuristics, not universal laws. Audible loss of punch or groove
remains a stop condition even when numeric evidence is inconclusive.

## Mono retention

Mono retention is measured overall and by band:

```text
10*log10(
  power((L+R)/2) / mean(power(L), power(R))
)
```

`0 dB` is a fully coherent centre signal. Candidate-minus-reference is the
decision delta: a negative value means the derived candidate added cancellation
relative to its source.

Current configurable CLI defaults are:

```text
mono warning: -0.5 dB
mono failure: -1.5 dB
```

Numeric PASS never overrides mono listening or a confirmed loss of an important
instrument.

## Decoded codec peaks

Supported codec-preview profiles are:

```text
mp3_320
aac_256
aac_192
```

The active implementation performs a real encode, decodes to float WAV and
measures decoded true peak with FFmpeg. When a delivery target is supplied, it
can report a codec-specific trim recommendation. After applying any trim,
repeat the complete encode -> decode -> measure pass; never transfer one
codec's trim blindly to another.
