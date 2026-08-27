# Generative Audio Repair — source registry

Checked: 2026-08-27  
Scope: GitHub projects and Reddit evidence relevant to v0.6 Repair & Stem Lab.  
Related: #45, #50, #52, #54, #63.

## Evidence rules

- GitHub repositories/papers define candidate capabilities, reproducibility and integration risk.
- Reddit is used only to collect recurring symptoms, workflows and failure reports. It is not ground truth.
- A project score measures usefulness for Genre_test, not general product quality.
- No source may become a production dependency without revision/checkpoint pinning, a runtime smoke and project-owned fixtures.
- Repair quality and AI-origin detection are separate tasks.

Scores:

- 9–10: direct spike/benchmark candidate;
- 7–8: useful conditional backend/baseline;
- 5–6: supporting research;
- 1–4: weak evidence or unsafe universal advice.

## GitHub sources

| # | Source | Use in Genre_test | Main limitation | Score |
|---:|---|---|---|---:|
| 1 | [JusperLee/Apollo](https://github.com/JusperLee/Apollo) | Codec-like music restoration; band-split candidate for #63 | Trained mainly on MP3 degradation; SUNO transfer unproven | 10 |
| 2 | [NVIDIA/A2SB](https://github.com/NVIDIA/diffusion-audio-restoration) | 44.1 kHz bandwidth extension and local inpainting | Generative reconstruction and non-commercial terms; hallucination risk | 9 |
| 3 | [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | Maintained adapter for RoFormer/MDXC/MDX/Demucs models | Per-model licenses and CUDA/ONNX dependencies differ | 9 |
| 4 | [MVSEP-MDX23](https://github.com/ZFTurbo/MVSEP-MDX23-music-separation-model) | Strong 4-stem reference baseline | Old contest stack; repository/model licensing requires clarification | 8 |
| 5 | [Demucs v4](https://github.com/facebookresearch/demucs) | Recognized separation baseline and regression reference | Repository archived; not a new production center | 7 |
| 6 | [AudioSR](https://github.com/haoheliu/versatile_audio_super_resolution) | Probe for bandwidth extension to 48 kHz | Can invent high-frequency content and destabilize stereo | 7 |
| 7 | [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | Vocal-stem denoise/enhance experiment | Speech/mono domain; vocal identity can change | 7 |
| 8 | [VoiceFixer](https://github.com/haoheliu/voicefixer) | Vocal declip/denoise/dereverb research baseline | Older vocoder stack; strong identity/hallucination risk | 6 |
| 9 | [Matchering](https://github.com/sergree/matchering) | Deterministic reference-matching/mastering baseline | Not artifact repair; GPL and reference-selection dependency | 6 |
| 10 | [Sony CSL Audio Metrics](https://github.com/SonyCSLParis/audio-metrics) | Corpus-level FAD/kernel/density/coverage metrics | Set-level metrics cannot diagnose a local defect | 7 |
| 11 | [FORARTfe/HyMPS — AI Enhancing](https://github.com/FORARTfe/HyMPS/blob/main/Audio/AI-Enhancing.md) | Discovery list for restoration research | Curated list, not a verified backend | 5 |
| 12 | [FORARTfe/HyMPS — Treatments](https://github.com/FORARTfe/HyMPS/blob/main/Audio/Treatments.md) | Discovery list for deterministic DSP repair | Each linked project requires separate review | 5 |
| 13 | [AI Audio Datasets](https://github.com/Yuan-ManX/ai-audio-datasets) | Dataset discovery and clean/control candidates | Artificial composition is not equivalent to SUNO artifacts | 5 |
| 14 | [Neiro roadmap](https://github.com/ericcayers-ai/Neiro/blob/main/roadmap.md) | Replaceable graph-node architecture reference | Roadmap, not validated implementation | 5 |

## Reddit evidence

| # | Discussion | Useful observation | Project interpretation | Score |
|---:|---|---|---|---:|
| 15 | [Why Suno exports sound metallic](https://www.reddit.com/r/SunoAI/comments/1umfabi/why_your_suno_exports_sound_metallic_and_end_up/) | Repeated metallic top and translation complaints | Source for defect taxonomy and fixtures only | 8 |
| 16 | [Common Suno v4 issues](https://www.reddit.com/r/SunoAI/comments/1ila6pl/common_issues_in_sunoai_v4_how_to_fix_them/) | Harsh peaks, metallic percussion, weak bass, vocal dropouts | Do not convert suggested frequency bands into universal thresholds | 8 |
| 17 | [Stem splitter engineering follow-up](https://www.reddit.com/r/audioengineering/comments/1gbcyfn/follow_up_to_ai_stem_splitter_post/) | Separation can add clearly audible artifacts | Require full-mix baseline and reconstruction residual | 9 |
| 18 | [Suno stems introduce glitches](https://www.reddit.com/r/SunoAI/comments/1qyonka/anyone_else_notice_how_downloading_stems/) | Full mix can outperform the stem route | Preserve `FULL_MIX_WINS` verdict | 9 |
| 19 | [Why AI stems sound bad](https://www.reddit.com/r/SunoAI/comments/1lv5ywh/will_stems_ever_really_be_usable/) | Overlap causes smearing, bleed and musical noise | Estimated stems are derived evidence, never source truth | 9 |
| 20 | [Stems retain source artifacts](https://www.reddit.com/r/SunoAI/comments/1eaqwn9/you_can_now_get_separate_stems_instruments_vocals/) | Separation does not automatically remove original defects | Detect before and after separation | 8 |
| 21 | [Suno v5.5 remaster degradation report](https://www.reddit.com/r/SunoAI/comments/1vnu1tv/community_alert_suno_v55_remaster_engine/) | Reported harshness, low-mid loss, crushed dynamics and phase smear | Useful regression hypothesis; needs original audio and reproduction | 8 |
| 22 | [Suno v4 distortion workflow](https://www.reddit.com/r/SunoAI/comments/1jkx0hy/suno_v4_tips_reducing_instrumental_distortion_and/) | Regenerating a bad section can beat repeated repair | Preserve `REGENERATE_SOURCE` verdict | 7 |
| 23 | [Removing “Suno ambience”](https://www.reddit.com/r/SunoAI/comments/1fmkvmy/getting_rid_of_the_suno_ambiance_and_overall/) | Adaptive denoise may reduce sheen | Probe only; reject on transient/cymbal loss or pumping | 5 |
| 24 | [Cleaning Suno stems](https://www.reddit.com/r/SunoAI/comments/1r4gn2j/whats_the_best_way_to_clean_up_stems/) | Noise, hiss and instrument-stem artifacts recur | Fixture-discovery source, not a solution benchmark | 5 |
| 25 | [Hostile/noisy artifact thread](https://www.reddit.com/r/audioengineering/comments/1psxlu1/analyzing_the_specific_mix_artifacts_in_sunoai/) | Demonstrates sarcasm and fabricated precise EQ claims | Negative example for evidence filtering | 2 |
| 26 | [Universal 16 kHz cut / −14 LUFS recipe](https://www.reddit.com/r/SunoAI/comments/1qt9dod/title_guide_how_to_remove_suno_v5_metallic/) | One-setting-for-all advice | Do not implement as policy; may hide defects by removing useful signal | 3 |

## Consolidated engineering conclusions

1. There is no universal AI-artifact remover.
2. The default path is detect → localize → select eligible route → create Safe/Probe candidates → aligned loudness-matched review → damage guards.
3. Apollo and A2SB are restoration experiments, not source reconstruction truth.
4. Stem processing is conditional; the recombined full mix is the evaluated output.
5. AudioSR, Resemble Enhance and VoiceFixer remain Probe-only until stereo/vocal-identity gates pass.
6. Objective marker reduction cannot select a winner without musical-damage checks.
7. Ozone remains a separate v0.7 mastering boundary and is not part of the v0.6 repair benchmark.
8. No work in this registry targets detector evasion or provenance concealment.

## Required follow-up

- Keep detailed code/model/checkpoint terms and runtime findings in `GENERATIVE_AUDIO_REPAIR_TOP10_AUDIT.md`.
- Pin tested revisions and checkpoint hashes in processing manifests, not in this discovery registry.
- Recheck this registry before each backend graduation because upstream status changes.
