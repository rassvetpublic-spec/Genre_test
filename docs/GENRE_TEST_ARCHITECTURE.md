# Genre_test legacy/Ozone architecture supplement

Status: architecture supplement for legacy/Ozone integration. The canonical repository entry points remain `docs/ARCHITECTURE.md`, `docs/ACTIVE_CURRENT.md`, and the current roadmap; this document must not compete with or replace them.

## 1. Canonical system

`Genre_test` is the canonical engineering repository.

`OZONE12_MASTERING_LAB` is frozen legacy reference only. Its reusable knowledge is normalized into `docs/LEGACY_PROJECT_KNOWLEDGE.md` and ADRs under `docs/DECISIONS/`.

This supplement records the architecture implications of that migration. For current whole-product ownership, active work, retrieval status, repair/stems direction, and release state, follow the canonical entry points above.

## 2. Product boundary relevant to this supplement

Genre_test spans several independently useful but connected responsibilities. The parts relevant to this legacy/Ozone integration are:

1. **Audio understanding / profiling**
   - genre/family/style classification;
   - semantic instrumentation/vocal/production evidence;
   - BPM/key/source-format/DSP features;
   - validation, history and regression comparison.

2. **Catalog / search / retrieval**
   - the active v0.5 CLaMP/MERT retrieval lane;
   - persistent sidecar/catalog behavior defined by current repository contracts;
   - retrieval remains an independent product responsibility and is not subordinated to mastering.

3. **Mastering decision support**
   - evidence and guards for Ozone 12 mastering;
   - source/provenance validation;
   - transient/mono/codec/final-export checks;
   - future machine-readable recommendations.

Repair, stems, mastering orchestration, A/B/X and broader studio-finish capabilities remain roadmap responsibilities and are governed by the canonical roadmap/current-state documents rather than by this supplement.

Genre_test does **not** treat the classifier result as permission to activate mastering modules automatically without evidence.

## 3. Current analysis architecture

```text
Audio input
  |
  +-> source/container metadata
  |
  +-> analysis decode/resample
  |      |
  |      +-> MAEST Discogs519 --------------------+
  |      |     fine styles / broad families       |
  |      |                                         |
  |      +-> AudioSet AST --------------------+    |
  |      |     instruments/vocal/events       |    |
  |      |                                    |    |
  |      +-> DSP features --------------------|----+
  |            BPM/key/other measurements     |
  |                                           v
  +--------------------------------------> evidence fusion
                                                |
                                                v
                                           AudioProfile
                                                |
                     +--------------------------+-------------------------+
                     |                          |                         |
                     v                          v                         v
                 Normal view                SUNO view             Distributor view
```

Validation/regression retains access to raw MAEST results so product-layer changes do not silently redefine the historical baseline.

## 4. Source metadata and analysis-stream separation

Source properties and model input properties are separate concepts.

```text
Source metadata:
container / codec / sample rate / bit depth / channels / bitrate / duration

Analysis stream:
internal decoded/resampled representation used by MAEST/AST/DSP
```

A resampled internal stream must never be reported as the source file's native sample rate or bitrate.

## 5. Device/runtime architecture

Verified Blackwell runtime evidence inherited from the v0.4 acceptance work established this baseline unless a newer repository contract explicitly supersedes it:

```text
PyTorch 2.12.1+
CUDA 13.0 / cu130
Blackwell native architecture required when running on Blackwell
```

Runtime health must distinguish:

- Python/package health;
- CUDA availability;
- actual GPU name;
- active compute capability;
- native architecture availability in `torch.cuda.get_arch_list()`;
- FFmpeg availability;
- model revision/pin availability.

For Blackwell, `CUDA available=True` alone is insufficient; the active `sm_xxx` must be natively compiled into the installed PyTorch build.

## 6. Ozone mastering integration boundary

Ozone 12 Advanced is an **optional mastering backend** selected for the integration described by this supplement. REAPER is the reproducible render host when that Ozone backend is used. Ordinary analysis, catalog/search/retrieval, validation, and non-Ozone workflows must not require Ozone or REAPER.

The inherited mastering topology is represented as a **conditional slot map**, not as an always-on chain.

```text
Unlimiter
 -> Stem EQ / Master Rebalance
 -> EQ1
 -> Low End Focus
 -> Bass Control
 -> Vintage Compressor / Dynamics
 -> Impact
 -> EQ2 T/S
 -> Vintage Tape / Exciter
 -> Clarity
 -> Stabilizer
 -> Spectral Shaper
 -> Imager T/S
 -> Dynamic EQ
 -> Vintage Limiter
 -> Maximizer
```

`BYPASS` is a valid and often preferred result for any slot without a confirmed problem/job.

## 7. Mastering decision pipeline

Target architecture:

```text
AudioProfile + source provenance + mastering measurements
                       |
                       v
                problem/evidence map
                       |
                       v
              candidate module decision
                       |
                       v
              Ozone XML / render stage
                       |
                       v
              validation guard suite
                       |
            +----------+----------+
            |                     |
          PASS                  REJECT
            |                     |
            v                     v
      candidate/winner      rollback / refine
```

No module activation is justified by genre label alone. Genre/semantic evidence may select hypotheses, but measurements and A/B validation decide whether a stage survives.

## 8. Stage invariants

Every mastering stage should preserve these invariants:

- source audio provenance is known;
- current base/winner is explicit;
- active Ozone chain is determined from `ElementChain`;
- one primary problem/axis is changed at a time;
- previously accepted module blocks stay unchanged unless explicitly reopened;
- candidate is rendered from the original lossless source or one-time decoded lossy working PCM, not from the prior stage render;
- A/B is loudness matched;
- hard reject guards run before a stage is accepted;
- Maximizer/finalization remains last in the normal chain.

## 9. XML automation boundary

For the validated Ozone build:

```text
PresetVer = 6
PluginVer = 120002
PluginBuild = 1331
```

Known mappings may be automated. Unknown or build-sensitive ParamID/enum mappings require GUI-saved calibration evidence before automation.

Never infer an XML parameter map merely from a module name or from an `Enabled` field.

## 10. Output architecture

A single `AudioProfile` is the analysis result; Normal, SUNO and Distributor are presentation projections of the same evidence.

Default interactive behavior should favor a combined/auto presentation when the user wants all interpretations at once, while preserving explicit single-view selection for focused workflows.

Presentation changes must not re-run classifiers if the underlying `AudioProfile` already exists.

## 11. Validation architecture

Validation is a first-class layer, not post-processing decoration.

Required categories:

```text
input/source validation
runtime/model validation
classifier/regression validation
BPM/key/source-metadata validation
mastering-stage validation
mono/transient/codec validation
final export validation
```

Details live in `docs/VALIDATION_KNOWLEDGE.md`.

## 12. Separation of truth layers

```text
Raw evidence          = classifier/model/DSP measurements
Resolved profile      = deterministic fusion/policy result
Presentation view     = Normal/SUNO/Distributor wording
Mastering hypothesis  = optional candidate action
Mastering winner      = only after render + validation + listening
```

These layers must not be collapsed into one confidence score.
