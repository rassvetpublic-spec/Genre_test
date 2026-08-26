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

## Preprocessing identity v1

The first smoke reproduces the upstream audio policy deliberately:

```text
sample rate                  24000 Hz
channels                     mono
raw waveform normalization   false
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
clamp3-mert-24k-mono-5s-mean-v1
```

Any future change to these rules requires a new preprocessing identity and therefore a new embedding/cache identity.

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

## Explicit model-download gate

The bootstrap refuses the model-download step unless the user passes:

```powershell
-AcceptMertNonCommercialTerms
```

This is intentional. Model files are not bundled in Git or in the portable package.

## First hardware test

From the repository root on the target Windows machine:

```powershell
pwsh -File .\scripts\setup_clamp3_runtime.ps1 -Install
```

Then explicitly download the pinned model set:

```powershell
pwsh -File .\scripts\setup_clamp3_runtime.ps1 `
  -DownloadModels `
  -AcceptMertNonCommercialTerms
```

For the required real audio + Russian text smoke, use a normal readable WAV:

```powershell
pwsh -File .\scripts\setup_clamp3_runtime.ps1 `
  -RunSmoke `
  -AudioPath "D:\path\track.wav" `
  -Repeat 2
```

The evidence JSON is written under:

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
