# CLaMP 3 Retrieval Acceptance — v0.5

Status: **implementation/acceptance procedure**  
Parent epic: #26  
Integration block: #78  
Related issues: #30, #31, #32, #33, #35, #36, #39

This document defines the real-machine acceptance sequence after the CI-only fake-backend tests pass. It does not replace reviewed retrieval relevance data and does not authorize a full-catalog segment reindex before subset cost evidence is reviewed.

## 1. State boundary

Retrieval writes only to the flat project state:

```text
.genre_test\
├── logs\
├── models\
├── runtimes\clamp3\
├── upstream\clamp3\
├── history.sqlite3
└── retrieval.sqlite3
```

`history.sqlite3` remains the analysis/history source of existing `track_id` and AudioProfile metadata. Retrieval indexing must not rerun MAEST/AST solely to produce CLaMP vectors.

All default acceptance reports are written under `.genre_test\logs`.

## 2. Full-track catalog acceptance (#30/#39)

Start with a read-only audit:

```powershell
.\Genre_test_START.cmd retrieval-index-status
.\Genre_test_START.cmd retrieval-catalog-audit
```

Then use the existing full-track incremental index path. For a pilot:

```powershell
.\Genre_test_START.cmd retrieval-index --limit 20
.\Genre_test_START.cmd retrieval-index --limit 20
```

Acceptance for the second unchanged pilot pass:

- `embedded == 0`;
- unchanged rows are cache hits;
- no MAEST/AST rerun is triggered;
- the retrieval DB remains readable;
- no new corrupt rows are reported.

For the real catalog, release acceptance requires >=99% coverage of **readable source paths**, or an explicit explanation for every remaining failure. Missing source files are reported separately and do not count as inference failures.

Retry only readable rows that still lack the active backend embedding:

```powershell
.\Genre_test_START.cmd retrieval-retry-missing --limit 20
```

Omit `--limit` only when a full retry pass is intended.

## 3. Segment subset gate (#33)

The baseline segment policy is versioned as:

```text
fixed30-hop30-cap64-min1-v1
```

Meaning:

- 30 s windows;
- 30 s hop;
- final tail retained only if >=1 s;
- files shorter than 1 s produce no segment embedding;
- maximum 64 windows per track;
- if a track exceeds the cap, windows are sampled deterministically across the full duration.

Check state before work:

```powershell
.\Genre_test_START.cmd retrieval-segment-status
```

Run a small real subset first:

```powershell
.\Genre_test_START.cmd retrieval-segment-index --limit 20
```

Record at minimum:

- selected/available/missing tracks;
- planned segments;
- segment cache hits/misses;
- newly embedded segments;
- source/inference failures;
- elapsed seconds;
- vector payload bytes;
- `retrieval.sqlite3` bytes.

Immediately repeat the exact same command:

```powershell
.\Genre_test_START.cmd retrieval-segment-index --limit 20
```

Second-pass acceptance:

- `embedded_segments == 0`;
- existing planned segments become cache hits;
- representative selection is deterministic;
- no new failures appear.

**Do not run** the following before reviewing subset cost evidence:

```powershell
.\Genre_test_START.cmd retrieval-segment-index --all
```

`--all` is deliberately explicit because segment indexing can multiply inference time/storage relative to one full-track vector per track.

## 4. Representative-segment acceptance

For each indexed track the representative selector computes the normalized centroid of that track's segment vectors and selects the segment with highest cosine to the centroid. Exact ties resolve to the earliest segment, then deterministic cache identity.

Search from a stored representative against full-track embeddings:

```powershell
.\Genre_test_START.cmd retrieval-search-representative TRACK_ID --target-scope full --top-k 20
```

Search representative-to-representative:

```powershell
.\Genre_test_START.cmd retrieval-search-representative TRACK_ID --target-scope representative --top-k 20
```

Manual acceptance should check whether representative search is more useful than full-track search for tracks with intros/outros, beat switches, or strongly changing arrangement. No quality claim is made before reviewed examples exist.

## 5. Custom interval acceptance

Example 60–90 s query:

```powershell
.\Genre_test_START.cmd retrieval-search-segment "C:\Music\track.wav" 60 90 --target-scope full --top-k 20
```

The interval must satisfy:

```text
0 <= start_s < end_s
end_s - start_s >= 1 s
```

The query vector is cached under the same backend fingerprint + content `track_id` + interval identity.

## 6. Stable retrieval exit codes (#35)

Print the current machine-readable contract:

```powershell
.\Genre_test_START.cmd retrieval-exit-codes
```

Baseline contract:

| Code | Meaning |
|---:|---|
| 0 | success |
| 20 | retrieval backend unavailable |
| 21 | required index/representative embedding missing |
| 22 | invalid query/arguments |
| 23 | source-file error |
| 70 | internal runtime error |
| 130 | user interruption / safe stop |

On interruption, already committed SQLite writes remain valid. A later incremental pass resumes from persisted cache rows.

## 7. Reviewed benchmark schema (#36)

Benchmark relevance is independent from normal analysis history. Scores are manually reviewed grades:

```text
0 = not relevant
1 = weak/partial relation
2 = relevant
3 = strongly relevant
```

Scores `2` and `3` count as relevant for Precision/Recall/MRR baseline calculations. nDCG uses the full graded 0..3 values.

Minimal **illustrative schema only** — replace all placeholder `track_id` values with reviewed real catalog identities before treating results as evidence:

```json
{
  "schema_version": 1,
  "name": "reviewed-ru-en-v1",
  "queries": [
    {
      "query_id": "ru-dark-electronic-01",
      "query_type": "text",
      "text": "мрачный электронный трек с плотными барабанами",
      "language": "ru",
      "paired_query_id": "en-dark-electronic-01",
      "relevance": {
        "PLACEHOLDER_TRACK_ID_A": 3,
        "PLACEHOLDER_TRACK_ID_B": 2,
        "PLACEHOLDER_TRACK_ID_C": 0
      }
    },
    {
      "query_id": "en-dark-electronic-01",
      "query_type": "text",
      "text": "dark electronic track with dense drums",
      "language": "en",
      "paired_query_id": "ru-dark-electronic-01",
      "relevance": {
        "PLACEHOLDER_TRACK_ID_A": 3,
        "PLACEHOLDER_TRACK_ID_B": 2,
        "PLACEHOLDER_TRACK_ID_C": 0
      }
    }
  ]
}
```

Run:

```powershell
.\Genre_test_START.cmd retrieval-benchmark-run "C:\path\reviewed_suite.json" --top-k 10
```

Default report family under `.genre_test\logs`:

- `retrieval_benchmark_*.json`
- `retrieval_benchmark_*.csv`
- `retrieval_benchmark_*.md`

Metrics:

- Precision@K;
- Recall@K;
- MRR;
- nDCG@K;
- paired RU/EN Top-K Jaccard overlap;
- embedding latency P50/P95;
- ranking latency P50/P95.

The release benchmark target remains >=50 reviewed queries, with >=100 preferred. Placeholder/example labels are never considered ground truth.

## 8. Backup / restore

Before a large indexing pass:

1. close Genre_test and the retrieval sidecar;
2. back up `.genre_test\retrieval.sqlite3`;
3. if SQLite `-wal` / `-shm` files exist, either use SQLite backup semantics or copy only after all writers are stopped;
4. keep the pre-run copy until post-run `retrieval-catalog-audit` succeeds.

Restoration must happen with all Genre_test/retrieval processes stopped.

## 9. Exit gate for this integration block

The code block can be merged only after green CI, required exact-head review evidence, and `READY-MTD <exact-head-sha>` from `RELEASE_MANAGER`. The project's standing automatic MTD authorization may then execute the squash merge after immediate current-head revalidation; an explicit user `mtd` remains a scoped override, not a mandatory extra gate.

Real-machine acceptance remains separate evidence:

- full-track catalog second-pass zero recomputation;
- >=99% readable full-track coverage or explained failures;
- segment subset timing/storage reviewed before `--all`;
- representative/custom-segment smoke on real CLaMP runtime;
- Cyrillic path/query smoke on Windows;
- reviewed RU/EN benchmark dataset created and run before retrieval-quality claims.
