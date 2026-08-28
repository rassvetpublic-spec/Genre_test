# 16. Suno v5.5 / Lossy-Source / T-S Mastering Protocol

Status: **universal procedure / evidence-informed, not a fixed preset**  
Added: 2026-08-28  
Scope: finished stereo AI-music sources, especially Suno v5.5, alternative-rock / dubstep / hybrid material, and cases where only an MP3/AAC source survives.

## 1. Evidence boundary

Suno states that v5.5 targets richer arrangements, sharper vocals and more dynamic sound. Community reports also describe recurring but non-universal failure modes: metallic/high-frequency texture, vocal sibilance/hiss, low-mid thinning, transient softening, crushed dynamics and phase smear. These reports are **hypotheses/fixture-discovery evidence**, not model specifications and not justification for fixed EQ cuts.

Relevant sources:

- Suno v5.5 release notes/blog: https://suno.com/release-notes/introducing-v5-5-voices-custom-models-and-my-taste
- iZotope Ozone 12 Unlimiter / IRC5 design: https://www.izotope.com/community/blog/inside-ozone-12
- iZotope mastering workflow and Low End Focus/Bass Control order: https://www.izotope.com/community/blog/how-to-master-a-song-from-start-to-finish
- iZotope transient/sustain imaging: https://www.izotope.com/community/blog/advanced-mastering-tips
- Community AI-artifact DSP reference with explicit transient protection: https://github.com/TheApeMachine/deshimmer
- Community Suno-oriented cleanup/mastering reference: https://github.com/henricksmedia/shimmer

Do not convert community frequency examples into universal thresholds. Detect/localize first.

## 2. Lossy-source exception

Preferred source remains native/lossless WAV. If no WAV exists and MP3/AAC is the only surviving source, mastering is still permitted under an explicit `LOSSY_SOURCE` provenance state.

Hard gate:

```text
LOSSLESS_AVAILABLE?
  YES -> use the lossless source; lossy files cannot replace it as mastering source.
  NO  -> allow declared LOSSY_SOURCE fallback.
```

Required procedure:

```text
lossy source
 -> decode once to PCM 32-bit float at source/native sample rate
 -> all analysis and stage renders from that PCM working copy
 -> never re-encode MP3/AAC between mastering stages
 -> final native WAV 24-bit / 48 kHz
 -> codec encode/decode audit only after final candidate
```

Rules:

- PCM decode does not restore information removed by the codec.
- Do not synthesize or boost missing `air` merely because the spectrum rolls off.
- High-frequency decisions near/above the codec cutoff have lower confidence.
- Stem separation, enhancement, bandwidth extension and resynthesis are derived repair routes, not source truth.
- Final metadata/report must state that the WAV master derives from a lossy source.

## 3. Full ordered module-slot template

The project keeps a stable **slot order** even when many modules are bypassed. This separates chain-order decisions from parameter decisions.

```text
01 Unlimiter                         [conditional restore]
02 Stem EQ / Master Rebalance       [conditional balance repair]
03 Equalizer 1                      [corrective / M-S]
04 Low End Focus                    [conditional attack/body contrast]
05 Bass Control                     [conditional low-end balance/punch/sustain]
06 Vintage Compressor / Dynamics    [optional macro glue]
07 Impact                           [microdynamic punch]
08 Equalizer 2                      [Transient/Sustain shaping]
09 Vintage Tape / Exciter           [optional nonlinear colour]
10 Clarity                          [optional T/S polish]
11 Stabilizer                       [adaptive balance, preferably T/S when useful]
12 Spectral Shaper                  [conditional de-harsh/de-shimmer]
13 Stereo Imager                    [prefer T/S for drum-forward hybrids]
14 Dynamic EQ                       [final corrective control; often M/S after widening]
15 Vintage Limiter                  [optional pre-final peak stage]
16 Maximizer                        [final loudness / true peak]
```

The existence of a slot is not permission to enable it. **BYPASS IS A VALID WINNER.**

Hard activation policy:

```text
16-slot template = topology/order map, NOT a default active chain
measured/listening problem absent -> BYPASS
module has no unique job -> BYPASS
benefit does not survive loudness-match/mono/transient/codec guards -> BYPASS
```

Every module must earn activation. The default active chain is the smallest problem-driven subset that solves the current source.

## 4. Recommended baseline for AI alt-rock / dubstep hybrid

Start with the smallest active set that addresses measured problems:

```text
EQ1
 -> Low End Focus       [only if low-end attack/body needs separation]
 -> Bass Control        [only if low-end balance/punch/sustain needs control]
 -> Impact
 -> EQ2 T/S
 -> Stabilizer T/S
 -> Spectral Shaper     [only if localized harsh/shimmer evidence exists]
 -> Imager T/S
 -> Dynamic EQ M/S
 -> Maximizer
```

Usually start bypassed unless evidence says otherwise:

```text
Unlimiter
Stem EQ / Master Rebalance
Vintage Compressor / Dynamics
Vintage Tape / Exciter
Clarity
Vintage Limiter
Stereoize
```

## 5. Unlimiter gate

Unlimiter belongs before corrective/mastering processing because its role is to reconstruct plausible gain around material affected by prior limiting. It is **not** a mandatory Suno stage.

Enable only when evidence supports flattened/shaved peaks or lost attack. If crest/event-aligned attack is already healthy, bypass it. Severe clipping/distortion is not automatically recoverable by Unlimiter.

## 6. Low-end order and T/S concept

For heavy hybrid material use this causal order when the modules are required:

```text
Low End Focus -> Bass Control -> Impact
```

Reasoning:

- Low End Focus changes the perceptual contrast between low-frequency attack and body.
- Bass Control then frames overall low-end level plus transient/sustained behavior.
- Impact shapes broader microdynamic punch after low-end behavior is stabilized.

Do not use this chain as an excuse to add bass. The goal is often **kick transient vs sub sustain separation**, not more low-frequency energy.

## 7. Core spatial model: focused transient, wider sustain

For drum-forward alternative-rock / dubstep hybrids, the preferred first hypothesis is:

```text
sub sustain          -> centered/stable
kick transient       -> centered/stable
snare front edge     -> focused
lead-vocal core      -> focused

guitar/synth body    -> wider
vocoder/doubles      -> wider when musically intended
reverb/granular tail -> wider
upper ambience       -> wider, subject to codec/harshness guards
```

This is a **directional strategy**, not a fixed width table.

Ozone T/S Imager is useful because it can leave drum positioning largely unchanged while widening ambience/sustain. Stereoize remains a separate probe, not a default master-wide widener.

## 8. T/S tonal strategy

`EQ2 T/S`, `Clarity T/S`, `Stabilizer T/S` and supported T/S Dynamic EQ can protect attack while working more strongly on sustained buildup.

Typical intent:

```text
Transient branch -> preserve kick/snare attack, consonants, pick/front edge
Sustain branch   -> control low-mid accumulation, long glass, reverb/body buildup
```

Do not assume all harshness is Sustain. S/T consonants, hats and clicks can be transient-localized; detect which branch carries the defect.

## 9. De-harsh / de-shimmer principle

AI-oriented community DSP projects provide a useful transferable idea: **artifact suppression must back off on legitimate transient attacks and broadband musical events**. The project therefore treats transient retention as a damage guard for Spectral Shaper/Dynamic EQ/repair passes.

Preferred procedure:

```text
localize artifact
 -> make conservative candidate
 -> loudness-match
 -> measure event-aligned attack retention
 -> inspect Side/Mid and mono
 -> listen to removed/delta signal when available
 -> reject if cymbal/drum/vocal-front damage exceeds artifact benefit
```

No universal `5–12 kHz cut` is accepted as policy.

## 10. Width after cleanup, final correction after width

General order:

```text
adaptive/spectral cleanup -> T/S Imager -> final M/S Dynamic EQ
```

Rationale: widening can expose or magnify Side-only fizz/phase problems. Final Dynamic EQ should therefore see the already-formed stereo field and may control Mid and Side differently.

If a cleanup process itself performs phase/stereo reconstruction, re-evaluate order by one-module A/B; do not assume the default.

## 11. Maximizer policy

Maximizer stays last in the baseline chain. Loudness is stopped by **musical damage**, not by a predetermined LUFS target.

Required guards:

- event-aligned transient attack after loudness matching;
- macro LRA/crest behavior;
- true peak;
- mono retention;
- decoded MP3/AAC peak and artifact audit.

For lossy-source projects, conservative true-peak headroom is preferred because the final WAV may later be encoded again. Exact ceiling is a delivery decision, not a universal constant.

## 12. What this protocol does not claim

- It does not claim every Suno v5.5 render has the same defect.
- It does not infer generator identity from an audio artifact.
- It does not make Reddit/GitHub observations ground truth.
- It does not require all 16 Ozone slots to be active.
- It does not claim MP3 can be converted back to a lossless original.
- It does not authorize fixed track-specific gain, threshold, width or LUFS values as universal defaults.

## 13. XML automation boundary

The full slot order may include modules whose Ozone 12.0.2 XML ParamID map has not yet been confirmed in the project. For those modules:

```text
slot/order = accepted architecture
parameter automation = NOT accepted until GUI-saved XML calibration confirms schema
```

Known T/S schema rules remain governed by `docs/13_CONFIRMED_XML_SCHEMA_BUILD_1331.md` and `docs/03_TRANSIENT_SUSTAIN_PROTOCOL.md`.
