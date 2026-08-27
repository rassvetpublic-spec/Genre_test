# CLaMP 3 P0 — selected runtime and real Windows smoke

Status: **implementation branch; hardware smoke still required before MTD**.

Related: #26, #27, #29, #41.

## Selected model path

For Genre_test audio retrieval the selected first production candidate is **CLaMP 3 SAAS**, not C2.

Reason:
- upstream documents SAAS as the recommended model for audio-based retrieval;
- upstream `config.py` defaults to the SAAS checkpoint;
- C2 is retained as the symbolic/MIDI/sheet-music candidate and is not part of the first audio-catalog runtime.

Pinned identity:

```text
CLaMP code:
  repo       https://github.com/sanderwood/clamp3.git
  revision   9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8

CLaMP SAAS weight:
  repo       sander-wood/clamp3
  revision   791815a04a3a2bd9ab64cf590ba8307930c179e6
  file       weights_clamp3_saas_h_size_768_t_model_FacebookAI_xlm-roberta-base_t_length_128_a_size_768_a_layers_12_a_length_128_s_size_768_s_layers_12_p_size_64_p_length_512.pth
  size       2571027658 bytes
  sha256     5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80
  license    MIT

MERT audio frontend:
  model      m-a-p/MERT-v1-95M
  revision   55fa29e5522049926c03d2ff9ae54d22c20e668f
  policy     treat as CC-BY-NC-4.0 / non-commercial gate for this project

Text encoder/tokenizer base:
  model      FacebookAI/xlm-roberta-base
  revision   e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
  license    MIT
```

The MERT revision is the commit explicitly recommended in the MERT model documentation for pinned loading. The project still applies the stricter current MERT license gate and does not treat this backend as commercially unrestricted.

## Preprocessing identity v2

The first smoke reproduces the upstream audio policy deliberately:

```text
sample rate                  24000 Hz
channels                     mono
raw waveform normalization   false
resampler                    scipy.signal.resample_poly 1.13.1
feature processor normalize  true
MERT window                  5.0 s
window overlap               0%
final chunk < 1 s            discard
MERT layer                   all layers
MERT reduction               mean
CLaMP audio max length       128 feature rows
CLaMP text max length        128 tokens
embedding dimension          768
final retrieval vector       L2 normalized
```

Version string:

```text
clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v2
```

The v2 identity replaces the un-runnable v1 bootstrap, which incorrectly required a nonexistent `torchaudio==2.12.1` cu130 wheel. Pinned upstream CLaMP/MERT does not import torchaudio. Any future change to these rules requires a new preprocessing identity and therefore a new embedding/cache identity.

## Runtime architecture

The first real test remains an isolated sidecar/runtime:

```text
Genre_test core .venv
  Python 3.11–3.13
  existing MAEST / AST runtime
          |
          | versioned protocol
          v
.genre_test/retrieval/
  runtime/.venv      Python 3.12
  upstream/clamp3    detached pinned checkout
  models/            explicit local model snapshots
  evidence/          hardware smoke JSON
```

The core `.venv` is not modified by the retrieval installer.

Target GPU stack for the first test:

```text
RTX 5070 Ti / sm_120
PyTorch 2.12.1
CUDA 13.0 / cu130
Python 3.12
```

## Development model-download behavior

During the v0.5 hardware/debug phase, the root launcher performs model download without an interactive confirmation prompt. The internal bootstrap flag remains an implementation detail, while the user-facing distribution/install acceptance flow is deferred to the v1.0 installer.

Model files are not bundled in Git or in the portable package. License/provenance remains recorded in the manifest, runtime doctor and `docs/THIRD_PARTY_MODELS.md`.

## First hardware test

All user-facing runtime operations go through the repository root launcher. PowerShell scripts under `scripts/` are internal implementation details and are not documented as user entry points.

From the repository root on the target Windows machine, inspect the optional retrieval state:

```powershell
.\Genre_test_START.cmd retrieval-status
```

Create the isolated Python 3.12 runtime and download the pinned model set:

```powershell
.\Genre_test_START.cmd retrieval-setup
```

The development launcher runs unattended and does not stop for an interactive license prompt.

For the required real audio + Russian text smoke, use a normal readable WAV:

```powershell
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
```

This command validates the complete boundary:

```text
Genre_test core .venv
  -> Clamp3SidecarBackend
  -> persistent JSON-lines sidecar
  -> isolated Python 3.12 runtime
  -> CLaMP 3 / MERT
```

A direct isolated-runtime diagnostic remains available through the same launcher:

```powershell
.\Genre_test_START.cmd retrieval-direct-smoke "D:\path\track.wav"
```

Evidence JSON is written under:

```text
.genre_test/retrieval/evidence/
```

## Required P0 evidence

Before #27/#29 can graduate, capture:

- Python / Torch / CUDA versions;
- CUDA device and native architecture availability;
- CLaMP checkpoint epoch/loss metadata;
- model-load latency;
- Russian text embedding latency;
- MERT + audio embedding latency;
- output vector norm;
- repeated text embedding cosine;
- repeated audio embedding cosine;
- text↔audio cosine for the smoke query;
- current and peak CUDA allocation;
- behavior after MAEST+AST have already run on CUDA;
- clean process exit and VRAM release.

Expected invariants:

```text
text norm          ~1.0
audio norm         ~1.0
repeat cosine      extremely close to 1.0
vector dimension   768
no core .venv mutation
```

Exact latency/VRAM thresholds are not guessed in advance; they are recorded from the RTX 5070 Ti evidence and become the baseline.

## CI boundary

CI must never download these multi-GB models.

CI only checks:
- immutable pin metadata;
- SHA helpers;
- script syntax/static gates;
- fake backend/storage/protocol behavior.

The real model/GPU smoke is a documented local release gate.
