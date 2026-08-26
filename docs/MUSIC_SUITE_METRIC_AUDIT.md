# Music Suite -> Genre_test metric audit

Status: design/audit for v0.5, related to #45.

Pinned upstream: `GeekatplayStudio/music-suite@8534963ccafa37dc23df84c6ac239132fba77d41` (MIT).

The goal is selective reuse of objective, testable DSP. Genre_test does **not** become a fork of the whole Music Suite application.

## 1. Existing overlap: keep Genre_test implementation

Genre_test already calculates these fields in `src/genre_test/features.py`:

- BPM / tempo-v2 behavior;
- key + major/minor mode using Krumhansl-Schmuckler profiles;
- RMS;
- spectral centroid;
- spectral rolloff;
- zero-crossing rate.

Music Suite or MusicMapper implementations of the same basic quantities are useful as comparison fixtures, but must not silently replace the current algorithms. Tempo in particular has an existing Genre_test short-loop ambiguity policy and independent regression history.

## 2. Promote into `TechnicalProfileOutputV1` first

These Music Suite metrics are objective enough to justify a v0.5 implementation spike once validated:

| Output | Upstream reference | Decision | Validation gate |
|---|---|---|---|
| sample peak / dBFS | `audioqi/core/metrics.py::peak, dbfs` | P1 adopt/port | synthetic exact-amplitude fixtures |
| integrated loudness LUFS | `loudness_integrated_lufs` | P1 adopt/port | EBU-style reference fixtures + pyloudnorm version pin |
| oversampled true peak estimate | `oversampled_true_peak` | P1 adopt/port | compare against known inter-sample-peak fixtures; label as estimate unless validated to delivery standard |
| crest factor dB | `crest_factor_db` | P1 adopt/port | impulse/sine/compressed fixtures |
| clipping segments | `clipping_segments` | P1 adopt/port | exact sample-position fixtures |
| DC offset | analyzer calculation + marker | P1 adopt/port | synthetic offset fixtures |
| stereo correlation timeline | `stereo_timelines` | P1 adopt/port | mono/in-phase/anti-phase fixtures |
| Mid/Side ratio timeline | `stereo_timelines` | P1 adopt/port | known M/S fixtures |
| L/R balance timeline | `stereo_timelines` | P1 adopt/port | channel-gain fixtures |
| spectral band balance | `spectral_balance` | P1 adopt/port | band-limited synthetic fixtures |
| spectrum curve | `spectrum_curve` | P1 optional | deterministic FFT/STFT fixtures |

### Target schema sketch

```text
TechnicalProfileOutputV1
  identity
    algorithm_bundle
    algorithm_revision
    dependency_versions
    sample_rate
  loudness
    integrated_lufs
  peaks
    sample_peak
    sample_peak_dbfs
    true_peak_estimate
    true_peak_dbfs
  dynamics
    rms
    crest_factor_db
  stereo
    correlation_timeline
    ms_ratio_db_timeline
    lr_balance_db_timeline
  spectral
    band_energy_ratios
    spectrum_curve_optional
  integrity
    dc_offset
    clipping_segments
  markers
    [...]
```

This object stays independent from `AudioProfile`, genre confidence, MAEST/AST evidence and CLaMP retrieval scores.

## 3. Marker system: useful, but calibrate thresholds

Music Suite has a good reusable architecture for merging flagged timeline windows into timestamped markers. Candidate marker types:

- `clipping`;
- `mono_incompatibility`;
- `dc_offset`;
- `loudness_dip`;
- `sibilance`;
- `harshness_band`;
- `sub_bass_heavy`;
- peak/true-peak risk.

The **marker representation and merge algorithm** are valuable immediately. The numerical thresholds are not automatically Genre_test truth.

Required before user-facing severity labels:

1. synthetic fixtures for deterministic boundaries;
2. reviewed real-music fixtures;
3. false-positive review across several genres;
4. absolute-energy context for ratio-based harshness/sub-bass markers;
5. no claim that a sample-peak envelope above -1 dBFS is itself a measured true peak.

The upstream project's own documentation notes that band-energy ratios compete arithmetically: reducing sub-bass can increase the *share* of 3–9 kHz energy without adding absolute high-frequency energy. Genre_test must preserve absolute context when using those ratios.

## 4. Second wave: benchmark before promotion

### Approximate LRA

Useful, but do not expose as standards-compliant LRA until the exact implementation and reference behavior are documented. If it remains an approximation, name it accordingly.

### Noise-floor estimate

Upstream uses a low-percentile short-window RMS heuristic. Useful as an engineering indicator, but source material without true silent passages can make it a content-floor estimate rather than recording noise floor. Keep wording explicit.

### Distortion proxies

High-frequency and harsh-band energy ratios are not direct distortion measurements. If retained, call them spectral ratios/proxies and never THD/distortion measurements.

## 5. Geometry Mapper: use for structure, not genre truth

The pinned Music Suite geometry mapper exposes frame-wise:

- RMS;
- spectral centroid;
- spectral bandwidth/spread;
- spectral rolloff;
- spectral flatness;
- ZCR;
- peak frequency;
- temporal edges;
- kNN edges over descriptor space;
- optional Demucs stem analysis.

Recommended Genre_test use:

```text
DSP frame/segment descriptors
        +
CLaMP segment embeddings
        +
tempo/change-point evidence
        ->
structure/change map
```

This supports #33 representative segments and #44 Tempo/Structure Map.

Do not use descriptor kNN as a replacement for CLaMP catalog similarity: they answer different questions. Descriptor distance is local timbral/energy geometry; CLaMP is semantic cross-modal retrieval.

## 6. Explicitly do not import into Genre_test core

- Music Suite web/Next.js UI;
- its database and run-management application;
- its mastering chain/optimizer;
- in-app updater;
- generic MCP server as a dependency;
- MusicMapper's small hard-coded CLAP label classifier;
- rule-based claims that overinterpret RMS/ZCR/centroid as genre, mastering quality or specific production technique.

The mastering algorithms may be studied separately for OZONE12_MASTERING_LAB, but Genre_test remains an analyzer/catalog/retrieval product.

## 7. Efficient implementation rule

Genre_test currently loads a mono waveform for analysis. TechnicalProfile needs stereo for meaningful correlation/M/S/LR balance.

Before implementation, refactor the decode boundary so one source decode can provide:

```text
canonical stereo waveform
  -> mono analysis view for MAEST/features
  -> stereo TechnicalProfile
  -> optional segment/retrieval views
```

Avoid decoding the same 10k-track catalog separately for MAEST, TechnicalProfile and CLaMP.

## 8. Recommended implementation order

1. Define `TechnicalProfileOutputV1` and metric identity contract.
2. Refactor/shared decode contract without changing v0.4 results.
3. Sample peak + RMS + crest + DC offset.
4. Stereo correlation + M/S + L/R balance.
5. Integrated LUFS.
6. True-peak estimate and validation.
7. Clipping + marker merge schema.
8. Spectral band ratios.
9. Calibrated harshness/sibilance/sub-bass markers.
10. Frame/segment geometry feeding #44/#33.

## 9. FAR TODO boundary updated

Objective measurable parts of the former "Production/Mix Profile" may move into #45 through this document. Subjective interpretation remains FAR TODO:

- `pristine` / `professional`;
- `raw`;
- `punchy`;
- `tube-like`;
- exact reverb type;
- exact plugin/processing-chain inference;
- creative mastering advice.

Those descriptors require independent calibration and must never be inferred solely from one technical ratio.
