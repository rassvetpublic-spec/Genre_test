from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from genre_test.retrieval import (
    MAX_TEXT_QUERY_CHARS,
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalHealth,
    RetrievalStore,
    SearchFilter,
    filter_track_ids,
    index_catalog,
    index_status,
    load_catalog_tracks,
    rebuild_catalog,
    search_audio,
    search_text,
    write_search_csv,
    write_search_json,
)
from genre_test.track_identity import identify_track


def _backend_info(version: str = "1") -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="fake-clamp",
        backend_version=version,
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
class FakeBackend:
    info: RetrievalBackendInfo
    vectors: dict[str, tuple[float, float, float]]
    text_vector: tuple[float, float, float] = (1.0, 0.0, 0.0)
    audio_calls: list[str] = field(default_factory=list)
    text_calls: list[str] = field(default_factory=list)

    def health(self) -> RetrievalHealth:
        return RetrievalHealth("OK", "fake", "ready", self.info.backend_name)

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        assert start_s is None and end_s is None
        self.audio_calls.append(track_id)
        identity = EmbeddingIdentity(
            backend_fingerprint=self.info.fingerprint,
            scope="full",
            track_id=track_id,
        )
        return EmbeddingVector.normalized(
            identity,
            self.vectors[track_id],
            expected_dim=3,
        )

    def embed_text(self, text: str, *, language: str | None = None) -> EmbeddingVector:
        self.text_calls.append(text)
        identity = EmbeddingIdentity.for_text(
            self.info.fingerprint,
            text,
            language=language,
        )
        return EmbeddingVector.normalized(
            identity,
            self.text_vector,
            expected_dim=3,
        )


def _profile(
    path: Path,
    *,
    family: str = "Electronic",
    genre: str = "Dance-pop",
    confidence: str = "high",
    bpm: float = 128.0,
    key: str = "B",
    mode: str = "minor",
    vocal: str = "Rapping",
    moods: list[str] | None = None,
    instruments: list[str] | None = None,
    production: list[str] | None = None,
) -> dict[str, object]:
    return {
        "path": str(path),
        "audio_features": {"bpm": bpm, "key": key, "mode": mode},
        "audio_profile": {
            "broad_family": family,
            "primary_genre": genre,
            "confidence": confidence,
            "vocal": vocal,
            "moods": moods or ["Tense"],
            "instruments": instruments or ["Synthesizer"],
            "production": production or ["Electronic music"],
        },
    }


def _write_history(
    history_path: Path,
    rows: list[tuple[str, Path, dict[str, object]]],
) -> None:
    with sqlite3.connect(history_path) as connection:
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
        for index, (track_id, path, payload) in enumerate(rows, 1):
            connection.execute(
                "INSERT INTO tracks(track_id, last_path) VALUES (?, ?)",
                (track_id, str(path)),
            )
            connection.execute(
                "INSERT INTO runs(run_id, track_id, analyzed_at, result_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    f"run-{index}",
                    track_id,
                    f"2026-08-27T00:00:{index:02d}Z",
                    json.dumps(payload, ensure_ascii=False),
                ),
            )


def _fixture_catalog(tmp_path: Path) -> tuple[Path, list[Path], list[str]]:
    files = [tmp_path / "a.wav", tmp_path / "b.wav", tmp_path / "c.wav"]
    for index, path in enumerate(files):
        path.write_bytes((f"audio-{index}" * 32).encode())
    track_ids = [identify_track(path).track_id for path in files]
    history = tmp_path / "history.sqlite3"
    _write_history(
        history,
        [
            (track_ids[0], files[0], _profile(files[0], bpm=128.0)),
            (track_ids[1], files[1], _profile(files[1], bpm=132.0)),
            (
                track_ids[2],
                files[2],
                _profile(
                    files[2],
                    family="Pop",
                    genre="Ballad",
                    bpm=90.0,
                    key="C",
                    mode="major",
                    vocal="Singing",
                    moods=["Calm"],
                    instruments=["Piano"],
                    production=["Acoustic"],
                ),
            ),
        ],
    )
    return history, files, track_ids


def test_schema_v1_migrates_to_v2_without_dropping_embeddings(tmp_path: Path) -> None:
    db = tmp_path / "retrieval.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE retrieval_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO retrieval_meta(key, value) VALUES('schema_version', '1')"
        )

    store = RetrievalStore(db)
    assert store.schema_version() == 2
    with store.connect() as connection:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='search_queries'"
        ).fetchone()
    assert row is not None


def test_incremental_second_pass_is_zero_recompute_and_path_move_is_cache_hit(
    tmp_path: Path,
) -> None:
    history, files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {
            track_ids[0]: (1.0, 0.0, 0.0),
            track_ids[1]: (0.9, 0.1, 0.0),
            track_ids[2]: (0.0, 1.0, 0.0),
        },
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")

    first = index_catalog(store=store, history_path=history, backend=backend)
    assert first.embedded == 3
    assert first.cache_hits == 0
    assert len(backend.audio_calls) == 3

    second = index_catalog(store=store, history_path=history, backend=backend)
    assert second.embedded == 0
    assert second.recomputed == 0
    assert second.cache_hits == 3
    assert len(backend.audio_calls) == 3

    moved = tmp_path / "moved-a.wav"
    files[0].replace(moved)
    with sqlite3.connect(history) as connection:
        connection.execute(
            "UPDATE tracks SET last_path = ? WHERE track_id = ?",
            (str(moved), track_ids[0]),
        )
    third = index_catalog(store=store, history_path=history, backend=backend)
    assert third.embedded == 0
    assert third.path_updates == 1
    assert len(backend.audio_calls) == 3
    stored = store.get(
        EmbeddingIdentity(
            backend_fingerprint=backend.info.fingerprint,
            scope="full",
            track_id=track_ids[0],
        )
    )
    assert stored is not None
    assert stored.path == str(moved)


def test_pilot_limit_is_resumable_and_full_followup_only_embeds_remaining(tmp_path: Path) -> None:
    history, _files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {track_id: (1.0, float(index), 0.0) for index, track_id in enumerate(track_ids)},
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")

    pilot = index_catalog(store=store, history_path=history, backend=backend, limit=1)
    assert pilot.catalog_tracks == 3
    assert pilot.selected_tracks == 1
    assert pilot.embedded == 1

    full = index_catalog(store=store, history_path=history, backend=backend)
    assert full.cache_hits == 1
    assert full.embedded == 2
    assert len(backend.audio_calls) == 3


def test_backend_change_is_stale_and_rebuild_keeps_old_backend_records(tmp_path: Path) -> None:
    history, _files, track_ids = _fixture_catalog(tmp_path)
    vectors = {
        track_ids[0]: (1.0, 0.0, 0.0),
        track_ids[1]: (0.9, 0.1, 0.0),
        track_ids[2]: (0.0, 1.0, 0.0),
    }
    old = FakeBackend(_backend_info("1"), vectors)
    new = FakeBackend(_backend_info("2"), vectors)
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=old)
    report = index_catalog(store=store, history_path=history, backend=new)

    assert report.stale_embeddings == 3
    assert store.stats(backend_fingerprint=old.info.fingerprint)["full"] == 3
    assert store.stats(backend_fingerprint=new.info.fingerprint)["full"] == 3

    rebuilt = rebuild_catalog(store=store, history_path=history, backend=new)
    assert rebuilt.embedded == 3
    assert store.stats(backend_fingerprint=old.info.fingerprint)["full"] == 3
    assert store.stats(backend_fingerprint=new.info.fingerprint)["full"] == 3


def test_stale_accounting_supports_more_than_sqlite_parameter_limit(tmp_path: Path) -> None:
    old = _backend_info("1")
    active = _backend_info("2")
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    identity = EmbeddingIdentity(
        backend_fingerprint=old.fingerprint,
        scope="full",
        track_id="track-1499",
    )
    store.put(
        EmbeddingVector.normalized(identity, (1.0, 0.0, 0.0), expected_dim=3),
        backend=old,
        path="old.wav",
    )
    track_ids = tuple(f"track-{index}" for index in range(2000))
    assert (
        store.count_stale(
            active_backend_fingerprint=active.fingerprint,
            track_ids=track_ids,
        )
        == 1
    )
    assert store.count_stale(
        active_backend_fingerprint=active.fingerprint,
        track_ids=(),
    ) == 0


def test_catalog_filters_cover_family_genre_bpm_key_vocal_tags_and_folder(tmp_path: Path) -> None:
    history, files, track_ids = _fixture_catalog(tmp_path)
    tracks = load_catalog_tracks(history)
    filters = SearchFilter(
        families=("Electronic",),
        genres=("Dance-pop",),
        keys=("B minor",),
        vocals=("Rapping",),
        moods=("Tense",),
        instruments=("Synthesizer",),
        production=("Electronic music",),
        source_folders=(str(tmp_path),),
        bpm_min=120.0,
        bpm_max=140.0,
        min_confidence=0.8,
    )
    assert filter_track_ids(tracks, filters) == {track_ids[0], track_ids[1]}
    assert files[2].is_file()


def test_audio_and_russian_text_search_are_cached_deterministic_and_record_history(
    tmp_path: Path,
) -> None:
    history, files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {
            track_ids[0]: (1.0, 0.0, 0.0),
            track_ids[1]: (0.9, 0.1, 0.0),
            track_ids[2]: (0.0, 1.0, 0.0),
        },
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=backend)

    audio_result = search_audio(
        store=store,
        history_path=history,
        backend=backend,
        audio_path=files[0],
        top_k=2,
    )
    assert audio_result.cache_hit
    assert audio_result.query_track_id == track_ids[0]
    assert [hit.track_id for hit in audio_result.hits] == [track_ids[1], track_ids[2]]

    query = "мрачный электронный трек с мощными барабанами"
    first_text = search_text(
        store=store,
        history_path=history,
        backend=backend,
        text=query,
        language="ru",
        top_k=2,
        filters=SearchFilter(families=("Electronic",)),
    )
    second_text = search_text(
        store=store,
        history_path=history,
        backend=backend,
        text=query,
        language="ru",
        top_k=2,
        filters=SearchFilter(families=("Electronic",)),
    )
    assert not first_text.cache_hit
    assert second_text.cache_hit
    assert backend.text_calls == [query]
    assert [hit.track_id for hit in first_text.hits] == [track_ids[0], track_ids[1]]
    assert [hit.track_id for hit in second_text.hits] == [track_ids[0], track_ids[1]]
    assert all(hit.family == "Electronic" for hit in first_text.hits)

    history_rows = store.search_history(limit=10)
    assert [row.query_type for row in history_rows[:3]] == ["text", "text", "audio"]
    assert history_rows[0].query_text == query
    assert history_rows[0].language == "ru"


def test_search_guards_empty_and_oversized_text(tmp_path: Path) -> None:
    history, _files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {track_id: (1.0, 0.0, 0.0) for track_id in track_ids},
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=backend)

    with pytest.raises(ValueError, match="must not be empty"):
        search_text(store=store, history_path=history, backend=backend, text="   ")
    with pytest.raises(ValueError, match="too long"):
        search_text(
            store=store,
            history_path=history,
            backend=backend,
            text="я" * (MAX_TEXT_QUERY_CHARS + 1),
        )


def test_search_recovers_from_corrupt_text_cache(tmp_path: Path) -> None:
    history, _files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {track_id: (1.0, 0.0, 0.0) for track_id in track_ids},
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=backend)
    query = "русский запрос"
    first = search_text(store=store, history_path=history, backend=backend, text=query, language="ru")
    assert not first.cache_hit
    identity = EmbeddingIdentity.for_text(backend.info.fingerprint, query, language="ru")
    with store.connect() as connection:
        connection.execute(
            "UPDATE embeddings SET vector_blob = ? WHERE cache_key = ?",
            (b"\x00" * 12, identity.cache_key),
        )
    second = search_text(store=store, history_path=history, backend=backend, text=query, language="ru")
    assert not second.cache_hit
    assert backend.text_calls == [query, query]


def test_index_status_reports_catalog_current_stale_and_missing_paths(tmp_path: Path) -> None:
    history, files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {track_id: (1.0, 0.0, 0.0) for track_id in track_ids},
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=backend, limit=2)
    files[2].unlink()

    status = index_status(
        store=store,
        history_path=history,
        backend_fingerprint=backend.info.fingerprint,
    )
    assert status.catalog_tracks == 3
    assert status.current_embeddings == 2
    assert status.current_missing == 1
    assert status.available_paths == 2
    assert status.missing_paths == 1


def test_json_and_csv_export_are_utf8_and_stable(tmp_path: Path) -> None:
    history, _files, track_ids = _fixture_catalog(tmp_path)
    backend = FakeBackend(
        _backend_info(),
        {
            track_ids[0]: (1.0, 0.0, 0.0),
            track_ids[1]: (0.9, 0.1, 0.0),
            track_ids[2]: (0.0, 1.0, 0.0),
        },
    )
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    index_catalog(store=store, history_path=history, backend=backend)
    result = search_text(
        store=store,
        history_path=history,
        backend=backend,
        text="электронный трек",
        language="ru",
        top_k=2,
    )

    json_path = write_search_json(result, tmp_path / "search.json")
    csv_path = write_search_csv(result, tmp_path / "search.csv")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["query_text"] == "электронный трек"
    assert len(payload["hits"]) == 2
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["track_id"] == track_ids[0]
