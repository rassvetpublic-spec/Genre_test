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

Candidate code pin for the initial compatibility spike:

```text
9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
```

Public Hugging Face model repository:

```text
sander-wood/clamp3
```

Observed license metadata:

```text
MIT
```

The model repository currently contains multiple multi-gigabyte weight variants. **The production weight variant is not yet selected.** #27 must benchmark and pin one exact filename/revision/SHA-256 before persistent embeddings are accepted.

One observed SAAS-weight LFS object is approximately 2.57 GB and exposes an LFS SHA-256 in the public model repository; this is research evidence only until the selected weight is finalized.

## MERT-v1-95M

Model:

```text
m-a-p/MERT-v1-95M
https://huggingface.co/m-a-p/MERT-v1-95M
```

Role:

CLaMP 3's documented audio preprocessing extracts MERT-compatible features before CLaMP audio encoding.

Observed model-card license:

```text
CC-BY-NC-4.0
```

This is materially different from Genre_test's MIT source license and from the CLaMP 3 MIT metadata.

Implications for current development policy:

- do not commit MERT weights into Genre_test;
- do not package MERT weights in portable ZIPs;
- download only when the user explicitly enables the retrieval component;
- retain attribution/provenance;
- treat the MERT-backed retrieval backend as experimental/non-commercial unless licensing is separately resolved;
- do not state that the complete retrieval model stack is commercially unrestricted.

### Revision choice

The MERT model repository has evolved over time and uses custom model code. A revision must be pinned before reproducible indexing.

The upstream MERT documentation historically recommended pinning a commit for security/reproducibility when `trust_remote_code=True`. #27 must select the exact revision after verifying compatibility with the CLaMP feature extractor.

No unpinned `main` model is accepted for release indexing.

## XLM-R

CLaMP 3 uses an XLM-R text backbone (`FacebookAI/xlm-roberta-base`) according to its model metadata/configuration.

Before release, #41 must record:

- exact model id/revision actually loaded by CLaMP;
- license metadata;
- whether tokenizer/model assets are downloaded indirectly;
- attribution if required.

## CLaMP research dependencies

The pinned upstream CLaMP snapshot references a research-oriented dependency set including older versions of Transformers/Accelerate and packages not needed by Genre_test core.

Policy:

- do not copy all upstream research dependencies into core `pyproject.toml` by default;
- install only runtime dependencies actually required by our inference adapter;
- keep them isolated until #27 proves a safe consolidation route;
- avoid dependencies used only for training/evaluation if inference does not require them.

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
Backend: CLaMP 3
Backend code revision: ...
CLaMP weight: ...
CLaMP weight SHA-256: ...
MERT model: m-a-p/MERT-v1-95M
MERT revision: ...
Text model: ...
Preprocessing version: ...
Embedding dim: ...
License summary: ...
```

## Release gate

Before v0.5 release:

- [ ] CLaMP code revision selected;
- [ ] CLaMP weight filename/revision/SHA selected;
- [ ] CLaMP license recorded;
- [ ] MERT revision selected;
- [ ] MERT license recorded;
- [ ] XLM-R provenance recorded;
- [ ] runtime-only dependency licenses reviewed;
- [ ] attribution text prepared;
- [ ] installer does not redistribute prohibited weights;
- [ ] README clearly states retrieval model terms;
- [ ] commercial/non-commercial status of the shipped retrieval configuration is explicit.
