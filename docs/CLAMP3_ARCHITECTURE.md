# CLaMP 3 Retrieval Architecture

Status: **proposed / implementation started**  
Epic: **#26**  
Runtime spike: **#27**

## Architectural principle

CLaMP 3 is a new **retrieval backend**, not a replacement classifier.

Existing v0.4 path stays authoritative for current profile outputs:

```text
Audio
 -> MAEST fine-style evidence
 -> AudioSet AST semantic evidence
 -> DSP / BPM / key / source metadata
 -> deterministic fusion
 -> AudioProfile schema 4
 -> Normal / SUNO / Distributor
 -> history / Validation / build comparison
```

New v0.5 path:

```text
Audio ---------------------------+
                                  |
                                  v
                           MERT-compatible frontend
                                  |
                                  v
                            CLaMP 3 audio encoder
                                  |
                                  +--> track embedding
                                  +--> segment embeddings
                                  +--> representative segment

Russian / multilingual text
        |
        v
CLaMP 3 text encoder
        |
        v
text embedding

track/text/segment embedding
        |
        v
versioned embedding store
        |
        v
exact cosine catalog index
        |
        +--> structured filters from AudioProfile/history
        |
        v
SearchHit[]
```

## Runtime boundary

The first implementation must treat CLaMP as optional.

Preferred provisional design while #27 is open:

```text
Genre_test core process
Python 3.11-3.13 / Torch 2.12.1 / cu130
        |
        | local machine-only subprocess protocol
        v
CLaMP sidecar runtime
upstream-compatible Python/Torch stack
        |
        +--> MERT
        +--> CLaMP 3
```

Why isolate first:

- upstream CLaMP requirements are older than core;
- upstream quick start targets Python 3.10/CUDA 11.8;
- core CUDA/Blackwell route is already released and tested;
- retrieval is optional;
- model/runtime faults must not break Analyze;
- large model lifecycle can be managed independently.

The sidecar decision is provisional until compatibility measurements in #27 are complete.

## Core / sidecar protocol

The core package owns stable contracts. The model-specific runtime implements them.

Conceptual operations:

```text
health
embed_audio
embed_text
shutdown
```

Proposed request metadata:

```json
{
  "protocol_version": 1,
  "request_id": "uuid",
  "operation": "embed_text",
  "payload": {
    "text": "мрачный электронный трек",
    "language": "ru"
  }
}
```

Response metadata:

```json
{
  "protocol_version": 1,
  "request_id": "uuid",
  "status": "ok",
  "backend": {...},
  "vector_ref": "temporary/local/vector.npy"
}
```

Large vectors should not be repeatedly serialized as verbose decimal JSON. A local binary/NPY transfer or another bounded binary transport is preferred after the spike.

## Model-output identity

Every embedding must be self-describing enough to decide whether it can be mixed with another vector.

Required backend identity:

```text
backend_name
backend_version
clamp_code_revision
clamp_weight_name
clamp_weight_sha256
mert_model_id
mert_revision
preprocessing_version
embedding_dimension
normalization
```

Required embedding identity:

```text
backend_identity
track_id or text-query identity
scope: full | segment | representative | text
start_s / end_s when applicable
generated_at
```

Vectors with different backend fingerprints must never be silently ranked in the same matrix.

## Normalization

Baseline retrieval contract is L2-normalized embeddings.

For vector `v`:

```text
v_norm = v / ||v||_2
```

Then ranking can use dot product as cosine similarity:

```text
score = query_norm @ candidate_norm
```

The normalization rule is part of backend identity.

## Storage

Retrieval state should be separate from existing history:

```text
.genre_test/
  history.sqlite3
  retrieval/
    retrieval.sqlite3
    vectors/
    index/
    cache/
```

Why separate DB:

- v0.4 history remains stable;
- vector schema can evolve independently;
- a retrieval reset does not destroy analysis history;
- embedding model revisions can coexist for comparison.

Proposed tables:

### `embedding_models`

One row per exact embedding backend identity.

Fields conceptually:

```text
model_key PK
backend_name
backend_version
clamp_revision
clamp_weight_sha256
mert_model_id
mert_revision
preprocessing_version
embedding_dim
normalization
created_at
metadata_json
```

### `track_embeddings`

```text
model_key
track_id
vector_location / vector_blob
vector_sha256
source_path_snapshot
generated_at
status
```

Unique key:

```text
(model_key, track_id)
```

### `segment_embeddings`

```text
model_key
track_id
start_s
end_s
vector_location
vector_sha256
representative
representative_score
generated_at
```

### `search_index_meta`

```text
index_id
model_key
vector_count
built_at
matrix_sha256
metadata_json
```

## Track identity

Use existing content-derived `track_id` where available.

Implication:

- moving a file does not require re-embedding identical bytes;
- renamed files can retain retrieval identity;
- path remains mutable catalog metadata;
- exact duplicates can be recognized separately from path identity.

## Full-track audio policy

CLaMP upstream supports long audio through MERT-derived features, but Genre_test must explicitly version how full-track audio is transformed.

Do not leave behavior implicit.

Preprocessing identity must include at least:

```text
sample rate
mono/stereo rule
normalization rule
window size
window overlap
MERT layer/reduction
long-track sampling/truncation rule
CLaMP token/sequence handling
```

Upstream code currently shows 24 kHz mono input and 5 s non-overlapping MERT windows in its extraction script. Genre_test may preserve or deliberately change this only with a new preprocessing version.

## Segment policy

Initial proposal for #33:

```text
segment size: 30 s
hop: configurable, initial 30 s
short tail: explicit skip/pad policy
very long track: deterministic cap/sampling if needed
```

Representative segment baseline:

```text
segments -> normalized embeddings
         -> centroid
         -> cosine(segment, centroid)
         -> argmax
```

Store both selected interval and score.

## Search engine

For the current catalog size, start with exact search.

At 10,500 tracks and 768 float32 dimensions:

```text
10,500 * 768 * 4 bytes ~= 30.8 MiB
```

A dense matrix is small enough that NumPy exact ranking should be interactive.

Do not add FAISS/HNSW until benchmark evidence requires it.

Stable ranking rule:

```text
1. similarity descending
2. track_id ascending
3. path ascending
```

This prevents nondeterministic equal-score ordering.

## Structured filtering

CLaMP similarity and existing profile metadata solve different problems.

Search pipeline:

```text
query embedding
 -> similarity scores
 -> optional candidate prefilter
 -> structured filter policy
 -> deterministic ranking
 -> SearchHit
```

Available structured fields can include:

- broad family;
- primary genre;
- distributor genre/subgenre;
- BPM range;
- key;
- profile confidence;
- mood;
- vocal;
- instruments;
- production;
- folder/path.

No need to encode every structured field into a vector.

## Failure isolation

Required behavior:

```text
CLaMP absent        -> Retrieval: N/A
CLaMP not installed -> Retrieval: N/A
CLaMP unhealthy     -> Retrieval: FAIL
index stale         -> Retrieval: WARN or stale search refusal by policy
core Analyze        -> remains usable
```

A retrieval embedding failure does not invalidate a previously valid `AudioProfile`.

## CI boundary

CI tests the contract, not multi-GB inference.

Use:

- fake deterministic backend;
- tiny vectors;
- protocol request/response fixtures;
- normalization/ranking tests;
- cache identity tests;
- SQLite migration tests.

Real CLaMP/MERT tests are local release evidence.

## Privacy

The intended design is local-first:

- user audio remains on the machine;
- model inference is local;
- text queries remain local;
- network access is only for explicitly needed package/model downloads unless future features state otherwise.

## Non-goals for first v0.5 implementation

- replacing MAEST/AST;
- cloud catalog service;
- vector database server;
- distributed index;
- automatic LLM query rewriting;
- silently using CLaMP zero-shot genre to change profile classification;
- claiming cosine similarity is calibrated relevance probability.
