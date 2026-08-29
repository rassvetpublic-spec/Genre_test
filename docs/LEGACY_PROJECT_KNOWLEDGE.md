# Legacy Project Knowledge: OZONE12_MASTERING_LAB → Genre_test

Status: **canonical legacy reference inside Genre_test**

## 1. Boundary

`OZONE12_MASTERING_LAB` is a frozen legacy project. No new engineering work, commits, branches, pull requests, issues, or architecture changes belong there.

All active development and all future interpretation of this knowledge happen in `Genre_test`.

The preserved legacy package is:

```text
legacy/OZONE12_MASTERING_LAB/OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_4_1.zip
```

The legacy package is evidence/reference, not a second source of truth competing with current `Genre_test` code and decisions.

## 2. What is retained

The following knowledge from Universal Core v1.4.1 is retained because it is track-independent and reusable:

- source/provenance gate for lossless vs lossy inputs;
- Ozone 12 module ordering/topology rules;
- `ElementChain` as the authority for active Ozone modules;
- confirmed Ozone XML/T-S schema constraints for the validated build;
- stage-by-stage, one-variable-at-a-time workflow;
- current-base/current-winner rule;
- transient/sustain mastering strategy;
- drum-attack protection;
- mono-survival and stereo-width guards;
- decoded codec-peak audit;
- native DAW/Ozone final-export authority;
- hard reject conditions and validation heuristics;
- automatic mastering meter concepts and output contracts;
- the rule that BYPASS is a valid winner.

The following are **not** promoted into Genre_test defaults:

- exact settings from one track;
- exact threshold/gain/width/LUFS values from one winner;
- calibration-only extreme probes;
- old prompts that conflict with later validated rules;
- unconfirmed Ozone ParamID mappings;
- assumptions that every AI/SUNO source has the same defects.

## 3. Source/provenance gate

Preferred source hierarchy:

```text
LOSSLESS_AVAILABLE?
  YES -> use native/lossless WAV/AIFF/FLAC as mastering source
  NO  -> allow an explicitly declared LOSSY_SOURCE fallback
```

For a declared lossy-only source:

```text
MP3/AAC
 -> decode once to PCM 32-bit float at native/source sample rate
 -> run all analysis and stage renders from that PCM working copy
 -> never lossy re-encode between stages
 -> final native WAV
 -> codec encode/decode audit only after the final candidate
```

A PCM decode of MP3/AAC does not restore information removed by the codec. High-frequency decisions near or above an observed codec cutoff have lower confidence.

## 4. Ozone 12 as mastering backend

The inherited full module-slot topology is:

```text
01 Unlimiter
02 Stem EQ / Master Rebalance
03 Equalizer 1
04 Low End Focus
05 Bass Control
06 Vintage Compressor / Dynamics
07 Impact
08 Equalizer 2 T/S
09 Vintage Tape / Exciter
10 Clarity
11 Stabilizer
12 Spectral Shaper
13 Stereo Imager T/S
14 Dynamic EQ
15 Vintage Limiter
16 Maximizer
```

This topology is an **order map**, not a default active chain.

Hard rule:

```text
problem absent -> BYPASS
module has no unique job -> BYPASS
benefit fails loudness-match / mono / transient / codec guards -> BYPASS
```

The preferred active chain is always the smallest problem-driven subset.

## 5. Confirmed XML boundary

The legacy core validated the main T/S mapping for:

```text
PresetVer = 6
PluginVer = 120002
PluginBuild = 1331
```

Known transferable rules:

- active chain must be decoded from `Global/ExtraBytes ElementID="ElementChain"`;
- `Enabled=1` alone is not authoritative for chain membership;
- Equalizer, Clarity, Stabilizer, Stereo Imager and Dynamic EQ have confirmed T/S behavior for the validated build;
- Impact and Maximizer must not be assigned invented Main/Aux T/S parameter maps;
- unknown ParamID/enum mappings are not automated until GUI-saved calibration evidence exists;
- if the Ozone build changes, revalidate only build-sensitive/unknown mappings rather than re-calibrating already known fields blindly.

## 6. Stage workflow retained

The reusable workflow is:

```text
source gate
 -> inspect current audio + current base XML
 -> decode active ElementChain
 -> activate one problem/one module axis
 -> render from the original source/working PCM
 -> loudness-match A/B
 -> run technical guards
 -> select winner
 -> winner becomes next base
 -> preserve previously accepted modules
 -> Maximizer/finalization last
```

If a safe setting is nearly inaudible, one-module boundary probe is allowed to prove direction. The final winner then retreats from the extreme to the minimum musically sufficient setting.

Several modules must not be pushed simultaneously to make an effect audible; that destroys causality.

## 7. Current winner is the base

A GUI-saved/user-selected Ozone XML winner supersedes older generated candidates for the current track.

Subsequent stages must preserve already accepted module blocks and unknown data unless those blocks are explicitly in scope for the next change.

Diff scope is evidence.

## 8. Transient / Sustain strategy

For drum-forward and heavy hybrid material, the retained first hypothesis is:

```text
Transient branch -> protect kick/snare attack, consonants, pick/front edge
Sustain branch   -> control buildup, body, reverb, long glass/shimmer
```

Spatial first hypothesis:

```text
sub sustain          -> centered/stable
kick transient       -> centered/stable
snare front edge     -> focused
lead-vocal core      -> focused

guitar/synth body    -> wider when useful
vocoder/doubles      -> wider when intended
reverb/granular tail -> wider
upper ambience       -> wider only if mono/codec/harshness guards pass
```

This is a direction of investigation, not a fixed width preset.

Not all harshness is Sustain. Hats, clicks, sibilants and attack edges can be transient-localized and must be diagnosed before T/S processing is selected.

## 9. Low-end causal order

When the measured problem actually requires all three modules, the retained causal sequence is:

```text
Low End Focus -> Bass Control -> Impact
```

The purpose is separation of low-frequency attack/body and punch behavior, not automatic bass enhancement.

## 10. Width and mono-survival

Stereo widening is accepted only when important content survives mono.

Hard reject examples:

- important vocal/instrument noticeably disappears in mono;
- kick/bass stability is damaged;
- band-specific mono retention becomes materially worse;
- wow/headphone width improves while transient or codec translation degrades.

`Prevent Antiphase`, correlation and a vectorscope are evidence, not substitutes for a mono audit.

## 11. Maximizer/finalization lessons

Maximizer remains the final loudness/true-peak stage in the inherited baseline.

When the module becomes active, explicitly verify at least:

- mode;
- gain;
- margin/ceiling;
- true-peak behavior;
- linking;
- inherited Soft Clip;
- inherited Low Level Boost.

`Target Loudness` is not equivalent to the gain that actually drives loudness.

A planned LUFS target never outranks audible drum-attack/groove damage.

## 12. Native final and codec delivery

Final master authority:

```text
native DAW/Ozone export -> 24-bit WAV (delivery sample rate as specified)
```

A post-converted control WAV is diagnostic only when a native final is available.

If an accepted float render exists, sample/null comparison may be used to verify that the native 24-bit export differs only by expected low-level dither/noise behavior.

WAV true peak does not guarantee equal decoded peak after MP3/AAC encoding. Direct lossy delivery therefore requires real encode -> decode measurement and codec-specific trim/recheck when needed.

## 13. Legacy automatic mastering meter knowledge

The retained measurement model compares reference/base and candidate/final using at least:

- time alignment;
- analysis-only loudness/RMS matching;
- event-aligned transient attack;
- attack-to-sustain contrast;
- mono retention overall/event/by band;
- Side/Mid behavior;
- true/sample peak;
- decoded MP3/AAC peaks;
- duration, padding and tail integrity.

Legacy warning heuristics such as approximately `-0.5 dB` to `-1.0 dB` matched event-attack loss are review cues, not universal laws. Audible loss of punch remains the stronger stop condition.

## 14. Legacy source map

Primary source files inside Universal Core v1.4.1 that informed this document:

```text
docs/00_READ_FIRST_SOURCE_OF_TRUTH.md
docs/01_WORKFLOW_ALL_TRACKS.md
docs/03_TRANSIENT_SUSTAIN_PROTOCOL.md
docs/04_MODULE_PLAYBOOK.md
docs/06_METRICS_DECISION_LOGIC.md
docs/07_CODEC_AUDIT_AND_EXPORT.md
docs/14_VALIDATED_STAGE_AND_FINALIZATION_LESSONS.md
docs/15_AUTOMATIC_MASTERING_METER.md
docs/16_SUNO55_LOSSY_SOURCE_TS_MASTERING_PROTOCOL.md
tables/OZONE12_MASTERING_DECISION_HEURISTICS_v1_3.csv
tables/full_chain_slot_policy_v1_4.csv
checklists/FINAL_APPROVAL_CHECKLIST.md
```

The original package remains the archival evidence for exact XML schemas, tables, tools and examples.
