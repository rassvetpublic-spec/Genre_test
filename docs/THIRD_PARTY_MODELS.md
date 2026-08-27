# Third-Party Model Provenance

Status: **working record for v0.5**  
Issue: **#41**

This document records third-party model/code provenance separately from the MIT-licensed Genre_test source code.

It is not legal advice. It exists to prevent accidental redistribution or unsupported commercial claims.

## CLaMP 3

Project:

```text
CLaMP 3: Universal Music Information Retrieval Across Unaligned Modalities and Unseen Languages
https://github.com/sanderwood/clamp3
```

Selected code pin for the v0.5 P0 audio-retrieval spike:

```text
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

Public Hugging Face model repository:

```text
sander-wood/clamp3
```

Selected first audio-retrieval weight:

```text
variant    SAAS
revision   791815a04a3a2bd9ab64cf590ba8307930c179e6
file       weights_clamp3_saas_h_size_768_t_model_FacebookAI_xlm-roberta-base_t_length_128_a_size_768_a_layers_12_a_length_128_s_size_768_s_layers_12_p_size_64_p_length_512.pth
size       2571027658 bytes
sha256     5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80
license    MIT
```

SAAS is selected for the first audio-catalog runtime because the upstream project identifies the SAAS checkpoint as the audio-oriented/recommended path and its extraction configuration defaults to that checkpoint. The symbolic C2 checkpoint is not part of this first audio runtime.

The bootstrap verifies both the selected file size and SHA-256 before using the weight.

## MERT-v1-95M

Model:

```text
m-a-p/MERT-v1-95M
https://huggingface.co/m-a-p/MERT-v1-95M
```

Role:

CLaMP 3's documented audio preprocessing extracts MERT-compatible features before CLaMP audio encoding.

Selected compatibility pin for the first smoke:

```text
revision   55fa29e5522049926c03d2ff9ae54d22c20e668f
```

This revision is used because MERT's own historical model documentation explicitly recommended that commit as a pinned loading example, and it is compatible with the custom MusicHuBERT loader used by the pinned CLaMP preprocessing source. The real Windows smoke remains the final compatibility gate.

Current project licensing policy for this model:

```text
CC-BY-NC-4.0 / non-commercial gate
```

The project intentionally applies the stricter current MERT model-card terms to the selected runtime even though historical repository metadata may differ. This is materially different from Genre_test's MIT source license and from the CLaMP 3 MIT metadata.

Implications for current development policy:

- do not commit MERT weights into Genre_test;
- do not package MERT weights in portable ZIPs;
- download only when the user explicitly enables the retrieval component;
- the v0.5 development launcher downloads only when `retrieval-setup` is explicitly invoked and does not show an interactive prompt;
- retain attribution/provenance;
- treat the MERT-backed retrieval backend as experimental/non-commercial unless licensing is separately resolved;
- do not state that the complete retrieval model stack is commercially unrestricted;
- no unpinned `main` model is accepted for release indexing.

## XLM-R

CLaMP 3 uses an XLM-R text backbone.

Selected identity:

```text
model      FacebookAI/xlm-roberta-base
revision   e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
license    MIT
```

Both the model and tokenizer are loaded from this pinned local snapshot in the P0 runtime. The revision is part of the retrieval manifest/fingerprint so a future text-model or tokenizer change cannot silently reuse incompatible cached embeddings.

## Preprocessing identity

Selected preprocessing version:

```text
clamp3-mert-24k-mono-5s-mean-v1
```

Pinned behavior:

```text
sample rate                  24000 Hz
channels                     mono
raw waveform normalization   false
feature processor normalize  true
window                       5.0 s
window overlap               0%
final chunk < 1 s            discard
MERT layer                   all layers
MERT reduction               mean
CLaMP audio max length       128 feature rows
CLaMP text max length        128 tokens
embedding dimension          768
retrieval normalization      L2
```

Any change to these rules requires a new preprocessing identity and therefore a new embedding/cache identity.

## CLaMP inference dependencies

The upstream CLaMP repository contains a broader research/training dependency set. Genre_test does not copy that entire environment into core.

The isolated P0 runtime currently installs only the inference-oriented subset required by the selected path, including pinned Torch/Torchaudio, Transformers, Accelerate, NumPy, Hugging Face Hub, nnAudio, SoundFile, SentencePiece and supporting packages.

Policy:

- do not copy all upstream research dependencies into core `pyproject.toml`;
- install only runtime dependencies actually required by our inference adapter;
- keep them in the isolated Python 3.12 sidecar until #27 proves a safer consolidation route;
- avoid training/evaluation-only dependencies;
- complete a dependency-license inventory before v0.5 release.

## Model-download policy

Genre_test repository and portable release should contain:

```text
source code
bootstrap/install logic
model metadata/pins/checksums
```

They should not contain multi-gigabyte third-party model weights unless a future explicit redistribution review authorizes it.

## Provenance required in runtime diagnostics

Future `retrieval-doctor` should show at minimum:

```text
Backend: CLaMP 3 SAAS
Backend code revision: 9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
CLaMP weight revision: 791815a04a3a2bd9ab64cf590ba8307930c179e6
CLaMP weight SHA-256: 5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80
MERT model: m-a-p/MERT-v1-95M
MERT revision: 55fa29e5522049926c03d2ff9ae54d22c20e668f
Text model: FacebookAI/xlm-roberta-base
Text revision: e73636d4f797dec63c3081bb6ed5c7b0bb3f2089
Preprocessing version: clamp3-mert-24k-mono-5s-mean-v1
Embedding dim: 768
License summary: CLaMP MIT; XLM-R MIT; MERT non-commercial gate
```

## Release gate

Before v0.5 release:

- [x] CLaMP code revision selected;
- [x] CLaMP weight filename/revision/SHA selected;
- [x] CLaMP license recorded;
- [x] MERT revision selected;
- [x] MERT license policy recorded;
- [x] XLM-R provenance recorded;
- [ ] runtime-only dependency licenses reviewed;
- [ ] attribution text prepared;
- [x] development bootstrap does not redistribute model weights;
- [ ] v1.0 distribution installer adds the final user-facing model-term acceptance flow;
- [ ] README clearly states retrieval model terms;
- [ ] commercial/non-commercial status of the shipped retrieval configuration is explicit in final release notes.
