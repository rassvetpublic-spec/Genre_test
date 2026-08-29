# Genre_test Validation Knowledge

Status: reusable validation rules and regression knowledge

## 1. Validation principle

Validation exists to detect both technical failure and plausible-but-wrong interpretation.

Decision priority for mastering-related work:

1. hard technical rejects;
2. musical intent and audible damage;
3. loudness-matched preference;
4. metrics as evidence/risk detectors;
5. codec behavior for final delivery.

A metric winner is not automatically a musical winner.

## 2. Runtime/model validation

GPU validation must include more than `torch.cuda.is_available()`.

For the verified Blackwell baseline inherited from v0.4 acceptance work, verify unless a newer repository contract explicitly supersedes it:

```text
Torch >= 2.12.1
Torch build = cu130
CUDA runtime = 13.0.x
active GPU compute capability detected
active sm_xxx present in torch.cuda.get_arch_list()
```

On Blackwell this means an explicit native result such as `sm_120`, not only PTX/fallback execution.

Pinned MAEST and AudioSet AST revisions are part of reproducibility evidence.

## 3. Classifier validation

Keep raw MAEST validation comparable across releases.

Product-layer fusion and SUNO/Distributor presentation must not silently rewrite the historical raw-classifier baseline.

Useful regression checks:

- primary broad-family stability;
- top-style drift;
- confidence/classification drift;
- semantic evidence availability;
- MAEST/AST agreement/disagreement;
- output schema compatibility;
- deterministic result persistence/history.

## 4. Classical-music lesson

MAEST Discogs labels inside the `Classical` family must not be interpreted automatically as authoritative musicological period labels.

Examples such as `Classical---Romantic`, `Classical---Baroque` or `Classical---Contemporary` are model taxonomy outputs. They may correlate with period/style, but can be wrong for a specific composition/performance.

Therefore:

```text
Broad family = strong classifier evidence
Fine classical period/style = estimate, not historical ground truth
```

A future classical resolver may use dedicated evidence, but must preserve the original MAEST scores.

## 5. BPM validation

A mastering processor that does not time-stretch audio cannot physically change BPM merely by EQ/dynamics/stereo processing.

If two equal-duration renders of the same material produce materially different BPM estimates, first suspect beat-tracker ambiguity rather than actual tempo change.

Known ambiguity families include:

```text
half/double
2:3 / 3:2 metric level
syncopated breakbeat pulse
triplet/subdivision dominance
transient weighting changes after mastering
```

Validation rules:

- preserve multiple tempo candidates where ambiguity exists;
- compare duration before claiming a tempo change;
- use onset/periodicity evidence rather than one raw `beat_track()` number;
- mastering A/B should prefer a stable metric-level interpretation across variants of the same track;
- if the source name or trusted session metadata contains BPM, treat it as validation evidence, not as classifier input truth unless explicitly enabled;
- unexplained BPM-estimator divergence between equal-duration non-time-stretched variants is a **diagnostic / NEEDS-EVIDENCE condition**, not by itself a hard reject;
- promote BPM divergence to a hard reject only when independent timing, duration, or render evidence demonstrates an actual unintended tempo/timebase alteration.

## 6. Source-format validation

Never infer source bitrate/sample rate from the internally resampled analysis stream.

Source metadata must be read from the original file/container.

For uncompressed PCM WAV:

```text
nominal PCM bitrate = sample_rate * bit_depth * channels
```

Examples:

```text
44.1 kHz * 16 bit * 2 = 1411.2 kbps
48 kHz * 24 bit * 2 = 2304 kbps
```

Compressed-file bitrate must come from container/codec metadata or measured file properties, not the model sample rate.

## 7. Input/provenance validation

Hard source gate:

```text
lossless available -> lossless is mastering source
lossless absent    -> explicitly declare LOSSY_SOURCE and decode once to float PCM
```

For lossy-only provenance retain:

- source codec/container/bitrate when known;
- observed spectral cutoff/rolloff when measured;
- one-time decode identity;
- warning that HF confidence near/above the codec cutoff is reduced.

## 8. Stage audibility/causality validation

If a mastering stage is almost indistinguishable:

```text
verify active ElementChain
verify expected DSP ParamID changed
use Delta/Gain Match
run one-module boundary probe
confirm audible direction
retreat to minimum sufficient winner
```

Do not increase several modules at once to make the result obvious.

## 9. Drum-attack guard

For drum-forward material, compare the same aligned events after loudness matching.

Useful evidence:

- attack peak;
- attack RMS;
- attack-to-sustain contrast;
- short-time crest;
- macro LRA/section contrast.

Legacy review heuristic:

```text
~ -0.5 dB median matched attack loss -> warning region
~ -1.0 dB median matched attack loss -> strong warning/fail candidate
```

These are configurable heuristics, not universal laws. Audible loss of punch/groove is a stop condition regardless of planned loudness target.

## 10. Mono/stereo guard

Width is accepted only if the important content survives mono.

Compare candidate to reference:

- overall mono retention;
- event-window mono retention;
- band-specific mono retention;
- Side/Mid energy by relevant band;
- correlation/sample-aligned behavior;
- actual mono listening.

Suggested bands inherited from the legacy meter:

```text
20-120 Hz
120-500 Hz
500-4000 Hz
4000-18000 Hz
```

Important vocal/instrument disappearance in mono is a hard reject even if the stereo candidate sounds wider or more impressive on headphones.

## 11. Codec validation

Final delivery validation must use real encode -> decode paths.

Required checks can include:

- MP3 320 decode;
- AAC 256 decode;
- AAC 192 decode;
- decoded peak/true-peak behavior;
- duration/padding;
- start/tail integrity;
- mono and Side/Mid translation;
- transient retention.

A safe WAV ceiling does not guarantee a safe decoded MP3/AAC peak.

## 12. Final export validation

Native DAW/Ozone export is the authority when available.

Checklist:

- expected sample rate/bit depth;
- Normalize Off unless explicitly required;
- no unintended truncation/padding;
- if float winner exists, optional sample/null comparison;
- expected dither/noise-floor behavior only;
- codec audit after native final;
- final listening approval.

A post-converted control file does not replace a valid native final.

## 13. Hard rejects

Examples of universal hard rejects:

- invalid/corrupted XML;
- broken or unexpected `ElementChain`;
- wrong export format;
- clipping/decoded overs beyond the chosen delivery policy;
- important mono cancellation;
- clearly audible drum/punch destruction;
- independently verified unintended timing/duration/timebase alteration;
- source-format metadata reported from the analysis-resample stream;
- track-specific calibration values promoted as universal defaults.

BPM-estimator divergence alone is intentionally excluded from this list; see the diagnostic/NEEDS-EVIDENCE rule in section 5.

## 14. Knowledge promotion gate

A finding may enter canonical validation knowledge only when it is one of:

- reproducible schema fact;
- reusable procedure;
- formula/measurement definition;
- warning condition;
- hard reject;
- explicitly labeled heuristic with evidence and limits.

Exact per-track winner settings remain in track/session evidence, not here.
