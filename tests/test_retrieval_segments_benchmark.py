from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from genre_test.retrieval.benchmark import (
    BenchmarkQuery,
    BenchmarkSuite,
    QueryMetrics,
    _paired_overlap,
    query_metrics,
    write_benchmark_reports,
)
from genre_test.retrieval.catalog_acceptance import catalog_acceptance_report
from genre_test.retrieval.contracts import (
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalHealth,
)
from genre_test.retrieval.segment_store import SegmentMetadataStore
from genre_test.retrieval.segments import (
    SegmentPolicy,
    index_segments,
    plan_segments,
    segment_status,
    select_representative,
)
from genre_test.retrieval.service import SearchResult
from genre_test.retrieval.storage import RetrievalStore, StoredEmbedding


def _backend_info() -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="fake-segment",
        backend_version="1",
        clamp_code_revision="code",
        clamp_weight_name="weight.pth",
        clamp_weight_sha256="a" * 64,
        mert_model_id="mert",
        mert_revision="mert-rev",
        text_model_id="xlm",
        text_model_revision="xlm-rev",
        text_tokenizer_revision="xlm-rev",
        preprocessing_version="test-v1",
        embedding_dim=3,
    )


@dataclass
class FakeSegmentBackend:
    info: RetrievalBackendInfo = field(default_factory=_backend_info)
    calls: list[tuple[str, float | None, float | None]] = field(default_factory=list)

    def health(self) -> RetrievalHealth:
        return RetrievalHealth("OK", "fake", "ready", self.info.backend_name)

    def embed_text(self, text: str, *, language: str | None = None) -> EmbeddingVector:
        identity = EmbeddingIdentity.for_text(self.info.fingerprint, text, language=language)
        return EmbeddingVector.normalized(identity, (1.0, 0.0, 0.0), expected_dim=3)

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        self.calls.append((track_id, start_s, end_s))
        if start_s is None:
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="full",
                track_id=track_id,
            )
            values = (1.0, 0.0, 0.0)
        else:
            assert end_s is not None
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="segment",
                track_id=track_id,
                start_s=start_s,
                end_s=end_s,
            )
            slot = int(start_s // 30) % 3
            values = ((1.0, 0.0, 0.0), (0.8, 0.2, 0.0), (0.0, 1.0, 0.0))[slot]
        return EmbeddingVector.normalized(identity, values, expected_dim=3)


def _write_wav(path: Path, duration_s: float) -> None:
    sample_rate = 8_000
    frames = max(1, int(round(duration_s * sample_rate)))
    sf.write(path, np.zeros(frames, dtype=np.float32), sample_rate)


def _write_history(history: Path, rows: list[tuple[str, Path]]) -> None:
    with sqlite3.connect(history) as connection:
        connection.executescript(
            """
            CREATE TABLE tracks (
                track_id TEXT PRIMARY KEY,
                last_path TEXT
            );
            CREATE TABLE runs (
                run_id TEXT PRIMARY KEY,
                track_id TEXT NOT NULL,
                analyzed_at TEXT NOT NULL,
                result_json TEXT NOT NULL
            );
            """
        )
        for index, (track_id, path) in enumerate(rows):
            payload = {
                "path": str(path),
                "audio_features": {"bpm": 120 + index, "key": "B", "mode": "minor"},
                "audio_profile": {
                    "broad_family": "Electronic",
                    "primary_genre": "Dance-pop",
                    "confidence": "high",
                    "vocal": "Singing",
                    "moods": ["Tense"],
                    "instruments": ["Synthesizer"],
                    "production": ["Electronic music"],
                },
            }
            connection.execute(
                "INSERT INTO tracks(track_id, last_path) VALUES (?, ?)",
                (track_id, str(path)),
            )
            connection.execute(
                """
                INSERT INTO runs(run_id, track_id, analyzed_at, result_json)
                VALUES (?, ?, ?, ?)
                """,
                (f"run-{index}", track_id, f"2026-08-27T00:00:{index:02d}Z", json.dumps(payload)),
            )


def _stored_segment(
    backend: RetrievalBackendInfo,
    *,
    track_id: str,
    start_s: float,
    values: tuple[float, float, float],
) -> StoredEmbedding:
    identity = EmbeddingIdentity(
        backend_fingerprint=backend.fingerprint,
        scope="segment",
        track_id=track_id,
        start_s=start_s,
        end_s=start_s + 30.0,
    )
    vector = EmbeddingVector.normalized(identity, values, expected_dim=3)
    return StoredEmbedding(
        cache_key=identity.cache_key,
        identity=identity,
        path=f"{track_id}.wav",
        vector=vector,
        vector_sha256="a" * 64,
        created_at="2026-08-27T00:00:00Z",
    )


def test_segment_plan_fixed_windows_and_short_tail() -> None:
    windows = plan_segments(65.0)
    assert [(row.start_s, row.end_s, row.short_window) for row in windows] == [
        (0.0, 30.0, False),
        (30.0, 60.0, False),
        (60.0, 65.0, True),
    ]
    assert plan_segments(0.5) == ()


def test_segment_plan_cap_is_deterministic() -> None:
    policy = SegmentPolicy(max_segments=3)
    first = plan_segments(300.0, policy)
    second = plan_segments(300.0, policy)
    assert first == second
    assert len(first) == 3
    assert first[0].start_s == 0.0
    assert first[-1].start_s == 270.0


def test_representative_centroid_tie_uses_earliest_segment() -> None:
    backend = _backend_info()
    records = [
        _stored_segment(backend, track_id="a", start_s=30.0, values=(0.0, 1.0, 0.0)),
        _stored_segment(backend, track_id="a", start_s=0.0, values=(1.0, 0.0, 0.0)),
    ]
    selection = select_representative(records)
    assert selection.segment.identity.start_s == 0.0
    assert 0.70 < selection.score < 0.72


def test_segment_index_is_resumable_and_persists_representative(tmp_path: Path) -> None:
    audio = tmp_path / "тест.wav"
    _write_wav(audio, 65.0)
    history = tmp_path / "history.sqlite3"
    _write_history(history, [("track-a", audio)])
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    backend = FakeSegmentBackend()

    first = index_segments(store=store, history_path=history, backend=backend, limit=1)
    assert first.planned_segments == 3
    assert first.embedded_segments == 3
    assert first.segment_cache_hits == 0
    assert first.representative_updates == 1
    assert len(backend.calls) == 3

    second = index_segments(store=store, history_path=history, backend=backend, limit=1)
    assert second.embedded_segments == 0
    assert second.segment_cache_hits == 3
    assert len(backend.calls) == 3

    metadata = SegmentMetadataStore(store).get_representative(
        backend_fingerprint=backend.info.fingerprint,
        track_id="track-a",
        policy_version=SegmentPolicy().version,
    )
    assert metadata is not None
    assert metadata.start_s in {0.0, 30.0}

    status = segment_status(
        store=store,
        history_path=history,
        backend_fingerprint=backend.info.fingerprint,
    )
    assert status.segment_embeddings == 3
    assert status.representative_embeddings == 1
    assert status.represented_tracks == 1


def test_catalog_acceptance_reports_retry_and_coverage(tmp_path: Path) -> None:
    one = tmp_path / "one.wav"
    two = tmp_path / "two.wav"
    missing = tmp_path / "missing.wav"
    _write_wav(one, 2.0)
    _write_wav(two, 2.0)
    history = tmp_path / "history.sqlite3"
    _write_history(history, [("one", one), ("two", two), ("missing", missing)])
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    backend = FakeSegmentBackend()

    identity = EmbeddingIdentity(
        backend_fingerprint=backend.info.fingerprint,
        scope="full",
        track_id="one",
    )
    store.put(
        EmbeddingVector.normalized(identity, (1.0, 0.0, 0.0), expected_dim=3),
        backend=backend.info,
        path=str(one),
    )

    report = catalog_acceptance_report(
        store=store,
        history_path=history,
        backend_fingerprint=backend.info.fingerprint,
    )
    assert report.catalog_tracks == 3
    assert report.readable_paths == 2
    assert report.missing_paths == 1
    assert report.current_embeddings == 1
    assert report.retry_track_ids == ("two",)
    assert report.current_coverage == 0.5


def _search_result(track_ids: list[str]) -> SearchResult:
    from genre_test.retrieval.contracts import SearchHit

    backend = _backend_info()
    return SearchResult(
        query_type="text",
        backend_fingerprint=backend.fingerprint,
        top_k=len(track_ids),
        embedding_seconds=0.2,
        ranking_seconds=0.01,
        cache_hit=False,
        query_text="query",
        language="ru",
        query_track_id=None,
        filters=__import__("genre_test.retrieval.contracts", fromlist=["SearchFilter"]).SearchFilter(),
        hits=tuple(
            __import__("genre_test.retrieval.service", fromlist=["CatalogSearchHit"]).CatalogSearchHit(
                rank=index,
                track_id=track_id,
                path=f"{track_id}.wav",
                similarity=1.0 - index / 100,
                backend_fingerprint=backend.fingerprint,
                family=None,
                genre=None,
                confidence=None,
                bpm=None,
                key=None,
                vocal=None,
                moods=(),
                instruments=(),
                production=(),
            )
            for index, track_id in enumerate(track_ids, 1)
        ),
    )


def test_benchmark_metrics_and_reports(tmp_path: Path) -> None:
    query = BenchmarkQuery(
        query_id="ru-1",
        query_type="text",
        text="мрачный электронный трек",
        language="ru",
        relevance={"a": 3, "b": 2, "c": 0},
        paired_query_id="en-1",
    )
    metrics = query_metrics(query, _search_result(["a", "c", "b"]), top_k=3)
    assert metrics.precision_at_k == 2 / 3
    assert metrics.recall_at_k == 1.0
    assert metrics.reciprocal_rank == 1.0
    assert 0.0 < metrics.ndcg_at_k <= 1.0

    paired = BenchmarkQuery(
        query_id="en-1",
        query_type="text",
        text="dark electronic track",
        language="en",
        relevance={"a": 3, "b": 2, "c": 0},
        paired_query_id="ru-1",
    )
    suite = BenchmarkSuite(name="pair", queries=(query, paired))
    left = metrics
    right = QueryMetrics(
        query_id="en-1",
        query_type="text",
        precision_at_k=1.0,
        recall_at_k=1.0,
        reciprocal_rank=1.0,
        ndcg_at_k=1.0,
        embedding_seconds=0.1,
        ranking_seconds=0.02,
        result_track_ids=("a", "b", "d"),
    )
    overlap = _paired_overlap(suite, {"ru-1": left, "en-1": right})
    assert overlap == 0.5

    from genre_test.retrieval.benchmark import BenchmarkReport

    report = BenchmarkReport(
        suite_name="pair",
        backend_fingerprint=_backend_info().fingerprint,
        top_k=3,
        queries=(left, right),
        precision_at_k=0.8,
        recall_at_k=1.0,
        mrr=1.0,
        ndcg_at_k=0.9,
        paired_overlap_mean=overlap,
        embedding_p50_seconds=0.15,
        embedding_p95_seconds=0.2,
        ranking_p50_seconds=0.015,
        ranking_p95_seconds=0.02,
    )
    files = write_benchmark_reports(report, tmp_path / "отчёт")
    assert files["json"].is_file()
    assert files["csv"].is_file()
    assert files["markdown"].is_file()
    assert "Retrieval benchmark" in files["markdown"].read_text(encoding="utf-8")
