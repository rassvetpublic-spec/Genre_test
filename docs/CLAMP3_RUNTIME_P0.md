# CLaMP 3 P0 — selected runtime and final Windows hardware acceptance

Status: **hardware acceptance PASS on PR #72; merge still requires explicit MTD**.

Related: #26, #27, #29, #41.

## Final runtime decision

Genre_test v0.5 uses **CLaMP 3 SAAS through an isolated persistent subprocess sidecar**.

This is the selected production architecture for the retrieval layer:

```text
Genre_test core (.venv)
  -> JSON-lines protocol v1
  -> isolated Python 3.12 CLaMP sidecar
  -> CLaMP 3 SAAS + XLM-R + MERT
```

Rationale:

- stable MAEST/AST core keeps its existing PyTorch/CUDA environment;
- heavy retrieval dependencies remain isolated;
- CLaMP/MERT can be loaded lazily and shut down independently;
- model failure is contained behind structured sidecar errors;
- the target RTX 5070 Ti remains on a Blackwell-native Torch 2.12.1 + CUDA 13 route;
- no CLaMP model/runtime dependency is imported into the stable core at import time.

`core-native` inference was **not executed and is not claimed as PASS**. It is intentionally classified **N/A for the selected architecture**: after the isolated sidecar proved the required behavior, direct integration into the core environment was rejected as unnecessary risk. A future experiment may test it separately, but v0.5 does not depend on it.

## Pinned model identity

```text
CLaMP code
  repo       https://github.com/sanderwood/clamp3.git
  revision   9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8

CLaMP SAAS weight
  repo       sander-wood/clamp3
  revision   791815a04a3a2bd9ab64cf590ba8307930c179e6
  file       weights_clamp3_saas_h_size_768_t_model_FacebookAI_xlm-roberta-base_t_length_128_a_size_768_a_layers_12_a_length_128_s_size_768_s_layers_12_p_size_64_p_length_512.pth
  size       2571027658 bytes
  sha256     5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80

MERT audio frontend
  model      m-a-p/MERT-v1-95M
  revision   55fa29e5522049926c03d2ff9ae54d22c20e668f
  local sha  a2b8b747f72c06e0595aeae41ae5473f4364938c6b39b2c58be38c48e6bd3fcd

Text encoder/tokenizer
  model      FacebookAI/xlm-roberta-base
  revision   e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
```

## Corrected preprocessing identity v3

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
MERT weight_norm compat      mert-weight-norm-key-remap-v1
```

Version string:

```text
clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3
```

### MERT weight_norm compatibility

The pinned MERT checkpoint stores legacy PyTorch weight-norm keys:

```text
encoder.pos_conv_embed.conv.weight_g
encoder.pos_conv_embed.conv.weight_v
```

Modern PyTorch/Transformers expects:

```text
encoder.pos_conv_embed.conv.parametrizations.weight.original0
encoder.pos_conv_embed.conv.parametrizations.weight.original1
```

Genre_test performs a versioned **in-memory key remap only**. The source `pytorch_model.bin` is never rewritten and tensor values are not numerically changed.

Final hardware evidence proves:

```text
compat status                OK
source checkpoint modified   false
numerical weights changed    false
verified modern keys         2/2
missing_keys                 []
unexpected_keys              []
mismatched_keys              []
newly initialized warning    absent
```

A remaining Transformers warning says that a `mert_model` config is used to instantiate `music_hubert`. It is retained as diagnostic output, but it is not an acceptance failure because exact state-dict loading is independently verified with no missing, unexpected or mismatched keys.

## State layout

The logical Python module remains `src/genre_test/retrieval/`, but there is **no physical `.genre_test/retrieval/` data directory**.

Canonical state:

```text
.genre_test/
  logs/                       all logs / smoke / P0 JSON
  models/                     CLaMP / MERT / XLM-R assets
  runtimes/clamp3/.venv/      isolated Python runtime
  upstream/clamp3/            pinned upstream source
  history.sqlite3
  retrieval.sqlite3           persistent retrieval DB when used
```

Rules:

- `.genre_test/logs/` is the only diagnostic/report location;
- `.genre_test/models/` contains model assets;
- `.genre_test/runtimes/clamp3/` contains the isolated Python runtime;
- `.genre_test/upstream/clamp3/` contains the pinned upstream checkout;
- `.genre_test/retrieval/` is obsolete and must not exist;
- `src/genre_test/retrieval/` is source code, not a state directory.

## Automatic migration

`Genre_test_START.cmd retrieval-setup` migrates the previous development layout without re-downloading large assets when possible:

```text
.genre_test/retrieval/runtime/          -> .genre_test/runtimes/clamp3/
.genre_test/retrieval/models/           -> .genre_test/models/
.genre_test/retrieval/upstream/clamp3/  -> .genre_test/upstream/clamp3/
.genre_test/retrieval/retrieval.sqlite3 -> .genre_test/retrieval.sqlite3
.genre_test/retrieval/evidence/*        -> .genre_test/logs/
```

Migration refuses destructive merging when old and new destinations both contain competing state. The migrated isolated `.venv` is validated before reuse.

## User-facing commands

```powershell
.\Genre_test_START.cmd retrieval-status
.\Genre_test_START.cmd retrieval-setup
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-direct-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-p0-gate "D:\path\track.wav"
```

## CPU behavior

The isolated runtime resolves CUDA when available and otherwise can execute on CPU. CPU is a fallback/degraded route, not the P0 target route. The formal `retrieval-p0-gate` intentionally requires real MAEST + AST CUDA evidence and therefore fails on a CPU-only machine instead of silently treating CPU execution as the RTX hardware acceptance path.

CPU performance is not part of this P0 benchmark and remains a later portable/release validation item.

## Health/error boundary

The retrieval backend is optional and isolated from ordinary v0.4 analysis.

Health semantics are `OK / WARN / FAIL / N/A`. Missing assets/source and unavailable backends are represented structurally; sidecar inference failures do not alter MAEST/AST core execution. The sidecar protocol includes structured model/file missing, invalid-request, CUDA OOM and inference-failure errors.

CI uses no multi-GB downloads and exercises the pure-core/fake-backend contracts plus launcher, protocol, flat-layout, UTF-8 and error-state behavior.

## Final target-PC hardware evidence

Final hardened gate:

```text
Date                 2026-08-27
Git head             1cef99d04f440462b93739753330a63448724ea9
Audio                C:\GIT\TEST.wav
Duration             330.92 s
Source                WAV PCM_24 / 48 kHz / stereo
GPU                   NVIDIA GeForce RTX 5070 Ti
Runtime Python        3.12.10
Torch                 2.12.1+cu130
CUDA                  13.0
CLaMP dimension       768
Gate                  CLAMP3_P0_27_29
Result                PASS
```

### Core coexistence gate

MAEST and AudioSet AST ran first on CUDA:

```text
MAEST device                  cuda
MAEST windows                 3
AST status                    ok
AST device                    cuda
AST windows                   3
core gate subprocess          16.903 s
```

The core performance log for the final run recorded approximately:

```text
MAEST analyzer init           1.527 s
MAEST batch                   0.491 s / 3 windows
MAEST track total             6.794 s
AST init                      0.634 s
AST batch                     0.163 s / 3 windows
AST track total               1.161 s
```

### Direct isolated runtime

```text
CLaMP model load              5.554 s
text first                    1.561 s
text warm                     0.012 s
text repeat cosine            1.0
text norm                     1.0

MERT model load               1.586 s
audio first total             1.908 s
audio warm total              1.531 s
audio repeat cosine           0.99999988
audio norm                    0.99999994

CUDA allocated                2245018112 bytes
CUDA reserved                 2627731456 bytes
CUDA peak allocated           2437303808 bytes
```

### Persistent sidecar

```text
health/start latency           5.571 s
text first                     13.764 s   # includes lazy heavy model path
text warm                      0.013 s
audio first                    2.992 s    # includes lazy MERT path
audio warm                     1.654 s
text repeat cosine             1.0
audio repeat cosine            ~1.0

in-process CUDA allocated      2244815360 bytes
in-process CUDA reserved       2627731456 bytes
in-process CUDA peak           2437101056 bytes
process RSS                    5021597696 bytes
process running after close    false
external GPU MiB after close   0
```

Windows/WDDM did not provide useful per-process `nvidia-smi` memory before close, so **VRAM lifecycle acceptance does not rely on that value**. The authoritative proof is:

1. sidecar itself reports >2.24 GB live `torch.cuda.memory_allocated()` before close;
2. the sidecar process terminates after shutdown;
3. no process remains to own those CUDA allocations.

### Cross-path identity

Direct and sidecar paths agree within the gate tolerance:

```text
Russian text repeatability       PASS
audio repeatability              PASS
direct/sidecar text vector       PASS
direct/sidecar audio vector      PASS
text/audio cosine equality       PASS
text/audio cosine                ~0.10204336
L2 norms                         PASS
UTF-8 Russian transport          PASS
```

## #27 acceptance matrix

| Criterion | Status | Evidence |
|---|---|---|
| Reproducible written compatibility matrix | PASS | This document + pinned identities/runtime versions |
| Selected runtime architecture justified by evidence | PASS | Isolated persistent sidecar; real RTX hardware gate |
| No core PyTorch pin changes | PASS | Core remains Torch 2.12.1+cu130 |
| Small no-download CI health smoke | PASS | Existing no-download health/contract probes |
| Disabled/unavailable backend test coverage | PASS | Pure-core/fake backend and structured health/error tests in CI |

Additional task disposition:

| Task | Status |
|---|---|
| Modern isolated Windows runtime | PASS |
| Audio embedding | PASS |
| Russian text embedding | PASS |
| Repeatability | PASS |
| Cold/warm latency | PASS |
| VRAM/RAM | PASS |
| Run after MAEST+AST CUDA | PASS |
| Core-native inference | N/A — intentionally not selected; not claimed tested |
| Final runtime decision | PASS — isolated persistent sidecar |

The original spike requested exact initial environment-creation time and complete model-download time. Those two historical setup timings were not retained as normalized final metrics. This is recorded as an archival benchmark gap, not a correctness/architecture blocker; runtime identity, installed versions, model sizes/checksums, cold/warm inference, RAM/VRAM and CUDA coexistence are all captured.

## #29 acceptance matrix

| Criterion | Status | Evidence |
|---|---|---|
| Audio file -> normalized embedding | PASS | norm ~0.99999994 direct / ~1.0 sidecar |
| Russian text -> normalized embedding | PASS | norm 1.0 direct + sidecar |
| Same input repeatability | PASS | cosine >= 0.99999988 |
| Same pinned identity across paths | PASS | code/model revisions + backend/preprocessing fingerprints |
| UTF-8 Russian path | PASS | direct/sidecar text vector equality |
| Faithful pinned MERT load | PASS | in-memory remap, exact loading info, source unmodified |
| Clean missing/OOM/invalid/inference errors | PASS | structured sidecar error contract |
| Fake-backend tests separated from hardware smoke | PASS | CI remains no-download; hardware gate is local |
| Clean sidecar shutdown / VRAM lifecycle | PASS | in-process CUDA >0 before close + process terminated |

## CI boundary

PR #72 CI is green on Python 3.11, 3.12 and 3.13, including Ruff and pytest. CI intentionally does not download CLaMP/MERT/XLM-R multi-GB assets. The real model/GPU run remains a local hardware gate.

## P0 conclusion

The hardened target-PC gate is accepted as final hardware evidence for #27/#29. The selected v0.5 architecture is **isolated persistent CLaMP 3 SAAS sidecar with corrected MERT v3 preprocessing identity**.

Issues #27/#29 may be marked acceptance-complete, but PR #72 and the issue implementation state must remain unmerged/open until the user gives explicit **MTD**.
