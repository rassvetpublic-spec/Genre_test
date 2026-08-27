from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .backend import RetrievalBackend
from .contracts import SearchFilter
from .service import SearchResult, search_audio, search_text
from .storage import RetrievalStore

BENCHMARK_SCHEMA_VERSION = 1
RELEVANT_THRESHOLD = 2


@dataclass(frozen=True)
class BenchmarkQuery:
    query_id: str
    query_type: Literal["text", "audio"]
    relevance: dict[str, int]
    text: str | None = None
    language: str | None = None
    audio_path: str | None = None
    paired_query_id: str | None = None

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValueError("benchmark query_id must not be empty")
        if self.query_type == "text":
            if not self.text or not self.text.strip():
                raise ValueError("text benchmark query requires text")
            if self.audio_path is not None:
                raise ValueError("text benchmark query cannot carry audio_path")
        elif self.query_type == "audio":
            if not self.audio_path or not self.audio_path.strip():
                raise ValueError("audio benchmark query requires audio_path")
            if self.text is not None:
                raise ValueError("audio benchmark query cannot carry text")
        else:
            raise ValueError("benchmark query_type must be text or audio")
        if not self.relevance:
            raise ValueError("benchmark query requires reviewed relevance labels")
        for track_id, score in self.relevance.items():
            if not str(track_id).strip():
                raise ValueError("benchmark relevance track_id must not be empty")
            if score not in {0, 1, 2, 3}:
                raise ValueError("benchmark relevance labels must be 0..3")


@dataclass(frozen=True)
class BenchmarkSuite:
    name: str
    queries: tuple[BenchmarkQuery, ...]
    schema_version: int = BENCHMARK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != BENCHMARK_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported benchmark schema {self.schema_version}; "
                f"expected {BENCHMARK_SCHEMA_VERSION}"
            )
        if not self.name.strip():
            raise ValueError("benchmark suite name must not be empty")
        if not self.queries:
            raise ValueError("benchmark suite must contain at least one query")
        ids = [query.query_id for query in self.queries]
        if len(ids) != len(set(ids)):
            raise ValueError("benchmark query_id values must be unique")


@dataclass(frozen=True)
class QueryMetrics:
    query_id: str
    query_type: str
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float
    embedding_seconds: float
    ranking_seconds: float
    result_track_ids: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkReport:
    suite_name: str
    backend_fingerprint: str
    top_k: int
    queries: tuple[QueryMetrics, ...]
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    paired_overlap_mean: float | None
    embedding_p50_seconds: float
    embedding_p95_seconds: float
    ranking_p50_seconds: float
    ranking_p95_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": BENCHMARK_SCHEMA_VERSION,
            "suite_name": self.suite_name,
            "backend_fingerprint": self.backend_fingerprint,
            "top_k": self.top_k,
            "summary": {
                "precision_at_k": self.precision_at_k,
                "recall_at_k": self.recall_at_k,
                "mrr": self.mrr,
                "ndcg_at_k": self.ndcg_at_k,
                "paired_overlap_mean": self.paired_overlap_mean,
                "embedding_p50_seconds": self.embedding_p50_seconds,
                "embedding_p95_seconds": self.embedding_p95_seconds,
                "ranking_p50_seconds": self.ranking_p50_seconds,
                "ranking_p95_seconds": self.ranking_p95_seconds,
            },
            "queries": [
                {
                    **asdict(query),
                    "result_track_ids": list(query.result_track_ids),
                }
                for query in self.queries
            ],
        }


def load_benchmark_suite(path: Path) -> BenchmarkSuite:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise TypeError("benchmark suite root must be an object")
    raw_queries = payload.get("queries")
    if not isinstance(raw_queries, list):
        raise TypeError("benchmark suite queries must be a list")
    queries: list[BenchmarkQuery] = []
    for raw in raw_queries:
        if not isinstance(raw, dict):
            raise TypeError("benchmark query must be an object")
        relevance_raw = raw.get("relevance")
        if not isinstance(relevance_raw, dict):
            raise TypeError("benchmark query relevance must be an object")
        queries.append(
            BenchmarkQuery(
                query_id=str(raw.get("query_id", "")),
                query_type=str(raw.get("query_type", "")),  # type: ignore[arg-type]
                relevance={str(key): int(value) for key, value in relevance_raw.items()},
                text=str(raw["text"]) if raw.get("text") is not None else None,
                language=str(raw["language"]) if raw.get("language") is not None else None,
                audio_path=(
                    str(raw["audio_path"]) if raw.get("audio_path") is not None else None
                ),
                paired_query_id=(
                    str(raw["paired_query_id"])
                    if raw.get("paired_query_id") is not None
                    else None
                ),
            )
        )
    return BenchmarkSuite(
        name=str(payload.get("name", Path(path).stem)),
        queries=tuple(queries),
        schema_version=int(payload.get("schema_version", BENCHMARK_SCHEMA_VERSION)),
    )


def _dcg(labels: list[int]) -> float:
    return sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(labels))


def query_metrics(
    query: BenchmarkQuery,
    result: SearchResult,
    *,
    top_k: int,
) -> QueryMetrics:
    result_ids = [hit.track_id for hit in result.hits[:top_k]]
    labels = [query.relevance.get(track_id, 0) for track_id in result_ids]
    binary = [1 if label >= RELEVANT_THRESHOLD else 0 for label in labels]
    relevant_total = sum(
        1 for label in query.relevance.values() if label >= RELEVANT_THRESHOLD
    )
    precision = sum(binary) / top_k
    recall = sum(binary) / relevant_total if relevant_total else 0.0
    reciprocal_rank = 0.0
    for rank, relevant in enumerate(binary, 1):
        if relevant:
            reciprocal_rank = 1.0 / rank
            break
    ideal = sorted(query.relevance.values(), reverse=True)[:top_k]
    ideal_dcg = _dcg(ideal)
    ndcg = _dcg(labels) / ideal_dcg if ideal_dcg > 0 else 0.0
    return QueryMetrics(
        query_id=query.query_id,
        query_type=query.query_type,
        precision_at_k=precision,
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
        ndcg_at_k=ndcg,
        embedding_seconds=result.embedding_seconds,
        ranking_seconds=result.ranking_seconds,
        result_track_ids=tuple(result_ids),
    )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _paired_overlap(
    suite: BenchmarkSuite,
    metrics: dict[str, QueryMetrics],
) -> float | None:
    overlaps: list[float] = []
    seen: set[tuple[str, str]] = set()
    for query in suite.queries:
        if not query.paired_query_id or query.paired_query_id not in metrics:
            continue
        pair = tuple(sorted((query.query_id, query.paired_query_id)))
        if pair in seen:
            continue
        seen.add(pair)
        left = set(metrics[query.query_id].result_track_ids)
        right = set(metrics[query.paired_query_id].result_track_ids)
        union = left | right
        overlaps.append(len(left & right) / len(union) if union else 1.0)
    return statistics.fmean(overlaps) if overlaps else None


def run_benchmark_suite(
    *,
    suite_path: Path,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    top_k: int = 10,
    filters: SearchFilter | None = None,
) -> BenchmarkReport:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    suite = load_benchmark_suite(suite_path)
    selected_filters = filters or SearchFilter()
    metrics: list[QueryMetrics] = []
    suite_root = Path(suite_path).resolve().parent

    for query in suite.queries:
        if query.query_type == "text":
            result = search_text(
                store=store,
                history_path=history_path,
                backend=backend,
                text=query.text or "",
                language=query.language,
                top_k=top_k,
                filters=selected_filters,
            )
        else:
            audio_path = Path(query.audio_path or "")
            if not audio_path.is_absolute():
                audio_path = suite_root / audio_path
            result = search_audio(
                store=store,
                history_path=history_path,
                backend=backend,
                audio_path=audio_path,
                top_k=top_k,
                filters=selected_filters,
                exclude_self=False,
            )
        metrics.append(query_metrics(query, result, top_k=top_k))

    by_id = {metric.query_id: metric for metric in metrics}
    embedding_times = [metric.embedding_seconds for metric in metrics]
    ranking_times = [metric.ranking_seconds for metric in metrics]
    return BenchmarkReport(
        suite_name=suite.name,
        backend_fingerprint=backend.info.fingerprint,
        top_k=top_k,
        queries=tuple(metrics),
        precision_at_k=statistics.fmean(metric.precision_at_k for metric in metrics),
        recall_at_k=statistics.fmean(metric.recall_at_k for metric in metrics),
        mrr=statistics.fmean(metric.reciprocal_rank for metric in metrics),
        ndcg_at_k=statistics.fmean(metric.ndcg_at_k for metric in metrics),
        paired_overlap_mean=_paired_overlap(suite, by_id),
        embedding_p50_seconds=_percentile(embedding_times, 0.50),
        embedding_p95_seconds=_percentile(embedding_times, 0.95),
        ranking_p50_seconds=_percentile(ranking_times, 0.50),
        ranking_p95_seconds=_percentile(ranking_times, 0.95),
    )


def write_benchmark_reports(report: BenchmarkReport, prefix: Path) -> dict[str, Path]:
    target = Path(prefix)
    target.parent.mkdir(parents=True, exist_ok=True)
    json_path = target.with_suffix(".json")
    csv_path = target.with_suffix(".csv")
    md_path = target.with_suffix(".md")

    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "query_id",
                "query_type",
                "precision_at_k",
                "recall_at_k",
                "reciprocal_rank",
                "ndcg_at_k",
                "embedding_seconds",
                "ranking_seconds",
                "result_track_ids",
            ]
        )
        for query in report.queries:
            writer.writerow(
                [
                    query.query_id,
                    query.query_type,
                    query.precision_at_k,
                    query.recall_at_k,
                    query.reciprocal_rank,
                    query.ndcg_at_k,
                    query.embedding_seconds,
                    query.ranking_seconds,
                    "|".join(query.result_track_ids),
                ]
            )

    lines = [
        f"# Retrieval benchmark — {report.suite_name}",
        "",
        f"Backend fingerprint: `{report.backend_fingerprint}`",
        f"Top-K: {report.top_k}",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Precision@K | {report.precision_at_k:.6f} |",
        f"| Recall@K | {report.recall_at_k:.6f} |",
        f"| MRR | {report.mrr:.6f} |",
        f"| nDCG@K | {report.ndcg_at_k:.6f} |",
        f"| RU/EN paired overlap | {report.paired_overlap_mean if report.paired_overlap_mean is not None else 'N/A'} |",
        f"| Embedding P50, s | {report.embedding_p50_seconds:.6f} |",
        f"| Embedding P95, s | {report.embedding_p95_seconds:.6f} |",
        f"| Ranking P50, s | {report.ranking_p50_seconds:.6f} |",
        f"| Ranking P95, s | {report.ranking_p95_seconds:.6f} |",
        "",
        "Quality claims require reviewed relevance labels; model output alone is not ground truth.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "markdown": md_path}
