# CLaMP 3 P0 — selected runtime and real Windows smoke

Status: **hardware P0 PASS on RTX 5070 Ti; implementation PR #72 remains open pending MTD**.

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

MERT audio frontend:
  model      m-a-p/MERT-v1-95M
  revision   55fa29e5522049926c03d2ff9ae54d22c20e668f

Text encoder/tokenizer base:
  model      FacebookAI/xlm-roberta-base
  revision   e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
```

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

The selected runtime remains an isolated persistent sidecar:

```text
Genre_test core .venv
  Python 3.11–3.13
  MAEST / AST runtime
          |
          | versioned protocol
          v
.genre_test/retrieval/
  runtime/.venv      Python 3.12
  upstream/clamp3    detached pinned checkout
  models/            pinned local model snapshots

.genre_test/logs/
  genre_test.log
  clamp3_*.json      all CLaMP smoke / P0 diagnostics
```

**Storage rule:** runtime/assets stay under `.genre_test/retrieval`; all diagnostics, smoke reports and P0 result JSONs go only to the existing common `.genre_test/logs` directory. Do not recreate `.genre_test/retrieval/evidence` or per-test evidence directories.

The core `.venv` is not modified by the retrieval installer.

Validated GPU stack:

```text
RTX 5070 Ti / sm_120
PyTorch 2.12.1+cu130
CUDA 13.0
Python 3.12.10 retrieval runtime
```

## Development model-download behavior

During the v0.5 hardware/debug phase, the root launcher performs model download without an interactive confirmation prompt. Model files are not bundled in Git or in the portable package; provenance remains recorded in the specialized manifest/runtime documentation.

## Hardware gate command

All user-facing runtime operations go through the repository root launcher.

```powershell
.\Genre_test_START.cmd retrieval-status
.\Genre_test_START.cmd retrieval-setup
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-direct-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-p0-gate "D:\path\track.wav"
```

The P0 command validates the complete boundary:

```text
MAEST CUDA + AudioSet AST CUDA
  -> direct isolated CLaMP 3 SAAS + MERT
  -> repeated Russian text embedding
  -> repeated full-track audio embedding
  -> Genre_test core -> persistent sidecar
  -> process shutdown
  -> per-process VRAM release
```

All generated JSON diagnostics are written directly under:

```text
.genre_test/logs/
```

No test-specific result directories are created.

## RTX 5070 Ti P0 result — 2026-08-27

Input: `C:\GIT\TEST.wav`, 330.92 s, WAV PCM 24-bit / 48 kHz stereo.

Gate result: **PASS**.

Confirmed:
- MAEST executed on CUDA, 3 windows;
- AudioSet AST executed on CUDA, 3 windows, semantic status `ok`;
- CLaMP 3 direct runtime status `OK`;
- persistent sidecar status `OK`;
- Russian text repeat cosine `1.0`;
- direct audio repeat cosine `0.9999998808`;
- sidecar audio repeat cosine effectively `1.0`;
- text/audio vectors remained L2 normalized;
- sidecar shut down cleanly;
- sidecar per-process GPU memory after shutdown was `0 MiB`.

Direct runtime baseline:

```text
CLaMP load                6.65 s
Russian text cold         2.46 s
Russian text warm         0.012 s
MERT model load           1.44 s
full-track audio run #1   1.83 s
full-track audio run #2   1.49 s
CUDA peak allocated       ~2.44 GB
```

Sidecar baseline:

```text
health/startup             5.56 s
text cold                 13.93 s
text warm                  0.013 s
audio run #1               2.21 s
audio run #2               1.40 s
shutdown                   clean
VRAM after shutdown        0 MiB for sidecar PID
```

The hardware P0 evidence is sufficient to select the **isolated persistent sidecar** architecture for v0.5.

## Gate invariants

```text
text norm          ~1.0
audio norm         ~1.0
repeat cosine      >= 0.99999
vector dimension   768
MAEST device       cuda
AST device         cuda
sidecar shutdown   true
sidecar VRAM exit  0 MiB
no core .venv mutation
```

## CI boundary

CI must never download multi-GB model assets.

CI only checks:
- immutable pin metadata;
- SHA helpers;
- launcher/script regression gates;
- central log-directory policy;
- fake backend/storage/protocol behavior.

The real model/GPU smoke remains a local release gate.
