# External AI Music Detectors — validation references

Status: research reference / external validation candidates  
Issue: #129  
Recorded: 2026-08-29

## Purpose

This document records external AI-music-detection services that may be useful as independent comparison targets for the `AI Origin & Provenance Lab`.

They are **not** production truth, are not fused directly into `OriginProfileV1`, and must not be used as optimization targets for mastering/repair. Vendor accuracy claims are unverified until reproduced on a controlled Genre_test benchmark.

## Candidate services

| Service | Public entry point | Access model observed | Potential Genre_test use |
|---|---|---|---|
| authio / Forward Digital | https://authio.io/ai-music-checker | public checker; vendor also documents API access | convenient external point estimate / generator-family comparison |
| ACRCloud AI Music Detector | https://acrcloud.com/ai-music-detector/ | account/trial/API oriented | useful external comparison, including vendor-described full-mix/vocal/accompaniment analysis |
| IRCAM Amplify AIMD | https://www.ircamamplify.com/ | request-access / B2B-oriented | high-scale external validation candidate when access is available |
| Pex / Vobile AI Song Detector | https://pex.com/ai-song-detector/ | enterprise/demo/API oriented | rights-holder/UGC-oriented external comparison |
| Detector24 AI Music Detection | https://detector24.ai/products/ai-music-detection | account/trial/API oriented | scalable external score comparison |
| PesneGen | https://pesnegen.ru/analiz-treka-online | public upload analysis with extended reporting | accessible independent comparison and feature-report reference |

URLs, product behavior and access terms are date-sensitive. Re-check before any benchmark run.

## External disclosure / authorization gate

Uploading audio to any external detector discloses that audio to a third party. Local ownership, possession, or inclusion in a private benchmark does **not** by itself authorize that disclosure.

Before any upload, all of the following must be true:

1. the fixture is redistributable/public-domain **or** there is explicit purpose-specific authorization to disclose it to the named external service;
2. the current service terms/privacy information relevant to retention, training/model improvement, onward sharing and deletion have been reviewed to the extent available;
3. the reviewed data-handling terms are compatible with the fixture's license, disclosure authorization and benchmark purpose — for example, terms permitting retention, training/model improvement or onward sharing beyond those rights are **not** compatible merely because they are clearly stated;
4. the benchmark record identifies the exact service/product being used and the access date;
5. no private user audio, confidential material, or private-local benchmark corpus is uploaded merely because it is available locally.

If authorization is missing/unclear, terms are unavailable/unclear, or the reviewed data-handling terms are known to exceed the fixture's permitted disclosure/use, skip the external upload and record the service as `NOT_RUN_AUTHORIZATION_OR_TERMS` rather than weakening this gate.

## Validation protocol

When the disclosure gate and service access both permit the run, compare the same immutable **authorized** source set across services. Preserve:

- source SHA-256;
- generator/source-family truth when legitimately known;
- exact uploaded encoding;
- service name and access date;
- endpoint/API product name and version when exposed;
- advertised detector/model revision when exposed, otherwise explicit `UNKNOWN`;
- request/response identifier when exposed;
- raw response or a byte-preserved/structured response artifact when terms and privacy constraints permit retaining it;
- returned score/verdict semantics verbatim in structured evidence;
- whether attribution and/or human-vs-AI classification was returned;
- relevant retention/training/deletion terms or a dated reference to the reviewed terms;
- failures, unsupported files and rate/access limitations.

Recording revision identity matters because a vendor may change the detector behind a stable URL. A later score change must not be attributed to an audio transformation when the external backend revision is unknown or changed.

Suggested comparison set, **only when redistributable or explicitly authorized for the named service and compatible with that service's reviewed data-handling terms**:

```text
verified-human lossless controls
verified-human lossy controls
Suno examples across known versions with permitted external disclosure
Udio / other generator examples where provenance and disclosure authorization are known
ordinary mastering/codec derivatives retained under parent lineage
```

## Interpretation rules

- No vendor score is ground truth.
- Vendor-reported accuracy must be treated as a claim until independently reproduced.
- Disagreement between external services is useful evidence about benchmark difficulty, not a reason to majority-vote a verdict.
- Absence of a known AI fingerprint is not proof of human origin.
- Unknown/changed external detector revision is a benchmark confounder and must be reported explicitly.
- Do not tune Ozone, repair, codec, stereo or transient processing to lower external detector scores.
- Ordinary delivery/mastering robustness may be measured only to improve detector invariance and expose false positives/false negatives.

## Relationship to Genre_test

Canonical internal architecture remains `docs/AI_ORIGIN_PROVENANCE_LAB.md`. External services can serve as:

1. blind comparison baselines;
2. disagreement/challenge-set discovery;
3. generator-support reconnaissance;
4. external robustness sanity checks.

They do not replace the project's own verified-human FPR gates, LOGO evaluation, calibrated fusion, uncertainty handling or provenance rules.
