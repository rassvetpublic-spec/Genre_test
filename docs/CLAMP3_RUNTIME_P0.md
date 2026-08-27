# CLaMP 3 P0 — selected runtime and real Windows smoke

Status: **implementation PR #72; final hardware re-run required before MTD**.

Related: #26, #27, #29, #41.

## Selected model path

For Genre_test audio retrieval the selected first production candidate is **CLaMP 3 SAAS**.

Pinned identity:

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

Text encoder/tokenizer
  model      FacebookAI/xlm-roberta-base
  revision   e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
```

## Preprocessing identity v2

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

## Runtime architecture

The logical Python module remains `src/genre_test/retrieval/`, but there is **no physical `.genre_test/retrieval/` data directory**.

Canonical runtime state:

```text
.genre_test/
  logs/
    genre_test.log
    clamp3_*.json
    retrieval_p0_local_*.json

  models/
    clamp3-saas/
    mert-v1-95m/
    xlm-roberta-base/

  runtimes/
    clamp3/
      .venv/

  upstream/
    clamp3/

  history.sqlite3
  retrieval.sqlite3          # when persistent retrieval indexing is used
```

Rules:

- `.genre_test/logs/` is the only diagnostic/report location;
- `.genre_test/models/` contains model assets;
- `.genre_test/runtimes/clamp3/` contains the isolated Python runtime;
- `.genre_test/upstream/clamp3/` contains the pinned detached upstream checkout;
- `.genre_test/retrieval/` is obsolete and must not exist after migration;
- `src/genre_test/retrieval/` remains the source-code package and is unrelated to the removed data directory.

## Automatic migration

`Genre_test_START.cmd retrieval-setup` migrates the previous development layout without re-downloading model assets when possible:

```text
.genre_test/retrieval/runtime/          -> .genre_test/runtimes/clamp3/
.genre_test/retrieval/models/           -> .genre_test/models/
.genre_test/retrieval/upstream/clamp3/  -> .genre_test/upstream/clamp3/
.genre_test/retrieval/retrieval.sqlite3 -> .genre_test/retrieval.sqlite3
.genre_test/retrieval/evidence/*        -> .genre_test/logs/
```

The migration refuses destructive merging if both an old and a new destination already contain competing state. Once all known data is migrated, the obsolete `.genre_test/retrieval/` directory is removed.

The isolated `.venv` is validated after migration before it is reused.

## User-facing commands

```powershell
.\Genre_test_START.cmd retrieval-status
.\Genre_test_START.cmd retrieval-setup
.\Genre_test_START.cmd retrieval-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-direct-smoke "D:\path\track.wav"
.\Genre_test_START.cmd retrieval-p0-gate "D:\path\track.wav"
```

For an existing development installation, run `retrieval-setup` once after pulling the flat-layout change. It performs the layout migration before normal setup checks.

## Hardware P0 gate

The complete P0 sequence is:

```text
flat state-layout check
  -> MAEST CUDA
  -> AudioSet AST CUDA
  -> direct isolated CLaMP 3 + MERT ×2
  -> Russian text ×2
  -> full-track audio ×2
  -> core -> persistent sidecar ×2
  -> direct/sidecar cross-path equality checks
  -> shutdown
  -> VRAM release
```

Required invariants include:

```text
MAEST device                    cuda
AST device                      cuda
text/audio norm                 ~1.0
within-path repeat cosine       >= 0.99999
cross direct/sidecar text       match
cross direct/sidecar audio      match
cross text/audio cosine         match
vector dimension                768
sidecar shutdown                true
sidecar VRAM after shutdown     0 MiB
.genre_test/retrieval exists    false
```

## RTX 5070 Ti evidence history

The 2026-08-27 run on `C:\GIT\TEST.wav` already proved:

- MAEST CUDA;
- AudioSet AST CUDA;
- CLaMP/MERT direct audio inference;
- persistent sidecar audio inference;
- within-process repeatability;
- clean shutdown;
- zero per-process VRAM after sidecar shutdown.

Review of that report found that direct and sidecar audio vectors matched, but the Russian text vectors did not. Therefore the old PASS was intentionally **not accepted as final P0 closure**.

The sidecar now forces Python UTF-8 mode (`-X utf8`), and the gate requires direct/sidecar cross-path equality. One final real hardware run is required after the flat-layout migration.

## CI boundary

CI does not download multi-GB model assets. It checks:

- immutable pin metadata;
- launcher/script syntax and regression gates;
- flat state-layout policy;
- common log-directory policy;
- UTF-8 sidecar transport policy;
- fake backend/storage/protocol behavior.

The real model/GPU run remains a local release gate.
