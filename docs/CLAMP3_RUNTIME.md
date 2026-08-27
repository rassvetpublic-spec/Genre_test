# CLaMP 3 Runtime Spike

Issue: **#27**  
Status: **hardware validation in progress on PR #72**

## Objective

Determine the safest reproducible way to run CLaMP 3 beside the released Genre_test Windows runtime without destabilizing the v0.4 MAEST/AST analysis path.

## Core baseline

```text
Windows 11 x64
Python >=3.11,<3.14
PyTorch 2.12.1
CUDA 13.0 / cu130 for NVIDIA
RTX 5070 Ti / sm_120 verified
CPU-only core route supported
```

The v0.4 analysis environment remains independent from the optional CLaMP runtime.

## Selected experimental architecture

The current v0.5 candidate is an **isolated persistent subprocess sidecar**:

```text
Genre_test core .venv
       |
       | JSON-lines protocol / UTF-8
       v
.genre_test/runtimes/clamp3/.venv
       |
       +-- CLaMP 3 SAAS
       +-- MERT-v1-95M
       +-- XLM-R
```

Why this route is preferred for P0:

- no dependency mutation of the stable core `.venv`;
- independent Torch/model pins;
- explicit process lifecycle;
- GPU memory can be released by terminating the sidecar;
- protocol can be tested in lightweight CI;
- failures remain isolated from normal Analyze.

Core-native installation is not selected for v0.5 P0 because it provides no advantage that justifies risking the released MAEST/AST environment. The isolated route is the production candidate unless later benchmark data gives a concrete reason to revisit this decision.

## Canonical state layout

There is **no physical `.genre_test/retrieval/` data directory**.

```text
.genre_test/
  logs/
  models/
  runtimes/
    clamp3/
      .venv/
  upstream/
    clamp3/
  history.sqlite3
  retrieval.sqlite3
```

Logical source code remains under:

```text
src/genre_test/retrieval/
```

This source package name does not imply a matching state-data directory.

Storage rules:

- all diagnostics and JSON reports -> `.genre_test/logs/`;
- model assets -> `.genre_test/models/`;
- isolated runtime -> `.genre_test/runtimes/clamp3/`;
- pinned upstream source -> `.genre_test/upstream/clamp3/`;
- persistent retrieval DB -> `.genre_test/retrieval.sqlite3`;
- obsolete `.genre_test/retrieval/` must not remain after migration.

## Automatic development migration

The root launcher performs migration through:

```powershell
.\Genre_test_START.cmd retrieval-setup
```

Known old data is moved, not copied blindly:

```text
.genre_test/retrieval/runtime/          -> .genre_test/runtimes/clamp3/
.genre_test/retrieval/models/           -> .genre_test/models/
.genre_test/retrieval/upstream/clamp3/  -> .genre_test/upstream/clamp3/
.genre_test/retrieval/retrieval.sqlite3 -> .genre_test/retrieval.sqlite3
.genre_test/retrieval/evidence/*        -> .genre_test/logs/
```

If both the legacy and destination paths exist, migration stops rather than overwriting either copy. If unclassified content remains under the old directory, migration also stops rather than deleting it.

## Pinned candidate

```text
CLaMP code revision
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8

CLaMP 3 SAAS weight SHA-256
5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80

MERT
m-a-p/MERT-v1-95M
revision 55fa29e5522049926c03d2ff9ae54d22c20e668f

Text encoder/tokenizer
FacebookAI/xlm-roberta-base
revision e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
```

Target runtime:

```text
Python 3.12
PyTorch 2.12.1+cu130
CUDA 13.0
RTX 5070 Ti / native sm_120
```

## Audio preprocessing identity

```text
target sample rate           24000 Hz
mono                         true
raw waveform normalization   false
resampler                    scipy.signal.resample_poly
MERT window                  5 s
window overlap               0%
final chunk < 1 s            discard
MERT reduction               mean
embedding dimension          768
final retrieval vector       L2 normalized
```

Identity:

```text
clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v2
```

## Hardware evidence obtained

On the target Windows workstation, an initial run with `C:\GIT\TEST.wav` proved:

- core MAEST on CUDA;
- AudioSet AST on CUDA;
- real CLaMP 3/MERT audio inference;
- persistent sidecar inference;
- repeatability within direct and sidecar paths;
- normalized vectors;
- clean sidecar shutdown;
- sidecar per-process VRAM returned to `0 MiB` after shutdown.

Review of that evidence exposed one missing gate condition: the direct and sidecar **audio** vectors matched, but the same Russian **text** query produced different vectors between the two paths.

The old run is therefore not accepted as final P0 closure.

## UTF-8 correction

The persistent sidecar child now starts with Python UTF-8 mode:

```text
-X utf8 -u
```

The gate subprocess environment also enforces:

```text
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

The final P0 gate requires direct/sidecar agreement in addition to within-path repeatability:

```text
cross_text_head_match
cross_audio_head_match
cross_text_audio_cosine_match
```

## Final P0 sequence

User-facing command:

```powershell
.\Genre_test_START.cmd retrieval-p0-gate "D:\path\track.wav"
```

The sequence validates:

1. obsolete physical `.genre_test/retrieval/` is absent;
2. MAEST runs on CUDA;
3. AudioSet AST runs on CUDA;
4. direct isolated CLaMP text/audio inference repeats consistently;
5. persistent sidecar text/audio inference repeats consistently;
6. direct and sidecar paths agree for the same inputs;
7. sidecar exits cleanly;
8. per-process VRAM is released;
9. all generated diagnostics land in `.genre_test/logs/`.

## P0 completion checklist

- [x] target Windows hardware inventory captured;
- [x] CLaMP code revision pinned;
- [x] selected SAAS weight pinned;
- [x] MERT source/revision pinned;
- [x] Blackwell-native runtime proven;
- [x] real direct CLaMP/MERT audio smoke proven;
- [x] persistent sidecar audio smoke proven;
- [x] within-path repeatability measured;
- [x] shutdown/VRAM release measured;
- [x] flat state-layout migration implemented;
- [x] common log-folder policy implemented;
- [x] UTF-8 sidecar transport fix implemented;
- [ ] final flat-layout local migration run;
- [ ] final RU text cross-path equality PASS;
- [ ] final strengthened P0 gate PASS;
- [ ] #27/#29 closure recorded after evidence;
- [ ] PR merge only after explicit MTD.
