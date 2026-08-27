from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import SearchFilter

_CONFIDENCE_SCORE = {
    "low": 0.20,
    "low-medium": 0.40,
    "medium": 0.60,
    "medium-high": 0.80,
    "high": 1.00,
}


@dataclass(frozen=True)
class CatalogTrack:
    track_id: str
    path: str | None
    family: str | None
    genre: str | None
    confidence: str | None
    confidence_score: float | None
    bpm: float | None
    key: str | None
    vocal: str | None
    moods: tuple[str, ...]
    instruments: tuple[str, ...]
    production: tuple[str, ...]

    @property
    def path_exists(self) -> bool:
        return self.path is not None and Path(self.path).is_file()

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "path": self.path,
            "family": self.family,
            "genre": self.genre,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "bpm": self.bpm,
            "key": self.key,
            "vocal": self.vocal,
            "moods": list(self.moods),
            "instruments": list(self.instruments),
            "production": list(self.production),
        }


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(text for item in value if (text := _clean_text(item)) is not None)


def _track_from_row(row: sqlite3.Row) -> CatalogTrack:
    payload: dict[str, Any] = {}
    raw = row["result_json"]
    if raw:
        try:
            loaded = json.loads(str(raw))
            if isinstance(loaded, dict):
                payload = loaded
        except json.JSONDecodeError:
            payload = {}

    profile = payload.get("audio_profile")
    if not isinstance(profile, dict):
        profile = {}
    features = payload.get("audio_features")
    if not isinstance(features, dict):
        features = {}

    confidence = _clean_text(profile.get("confidence") or payload.get("confidence"))
    confidence_score = _CONFIDENCE_SCORE.get(confidence.lower()) if confidence else None
    key_name = _clean_text(features.get("key"))
    key_mode = _clean_text(features.get("mode"))
    key = " ".join(part for part in (key_name, key_mode) if part) or None

    bpm_raw = features.get("bpm")
    try:
        bpm = float(bpm_raw) if bpm_raw is not None else None
    except (TypeError, ValueError):
        bpm = None

    path = _clean_text(row["last_path"]) or _clean_text(payload.get("path"))
    return CatalogTrack(
        track_id=str(row["track_id"]),
        path=path,
        family=_clean_text(profile.get("broad_family") or payload.get("primary_genre")),
        genre=_clean_text(profile.get("primary_genre") or payload.get("resolved_genre")),
        confidence=confidence,
        confidence_score=confidence_score,
        bpm=bpm,
        key=key,
        vocal=_clean_text(profile.get("vocal")),
        moods=_clean_list(profile.get("moods")),
        instruments=_clean_list(profile.get("instruments")),
        production=_clean_list(profile.get("production")),
    )


def load_catalog_tracks(history_path: Path) -> list[CatalogTrack]:
    """Load one deterministic current catalog row per content-addressed track_id.

    Retrieval reuses the existing history track identity and latest known path/profile,
    but never writes retrieval state into the analysis-history database.
    """

    path = Path(history_path)
    if not path.is_file():
        return []
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if not {"tracks", "runs"}.issubset(tables):
            return []
        rows = connection.execute(
            """
            SELECT
                t.track_id,
                t.last_path,
                (
                    SELECT r.result_json
                    FROM runs AS r
                    WHERE r.track_id = t.track_id
                    ORDER BY r.analyzed_at DESC, r.rowid DESC
                    LIMIT 1
                ) AS result_json
            FROM tracks AS t
            ORDER BY t.track_id
            """
        ).fetchall()
    return [_track_from_row(row) for row in rows]


def catalog_by_track_id(history_path: Path) -> dict[str, CatalogTrack]:
    return {track.track_id: track for track in load_catalog_tracks(history_path)}


def filter_track_ids(
    tracks: list[CatalogTrack],
    filters: SearchFilter,
) -> set[str]:
    families = {value.casefold() for value in filters.families}
    genres = {value.casefold() for value in filters.genres}
    allowed: set[str] = set()

    for track in tracks:
        if families and (track.family is None or track.family.casefold() not in families):
            continue
        if genres and (track.genre is None or track.genre.casefold() not in genres):
            continue
        if filters.bpm_min is not None and (track.bpm is None or track.bpm < filters.bpm_min):
            continue
        if filters.bpm_max is not None and (track.bpm is None or track.bpm > filters.bpm_max):
            continue
        if filters.min_confidence is not None and (
            track.confidence_score is None
            or track.confidence_score < filters.min_confidence
        ):
            continue
        allowed.add(track.track_id)
    return allowed
