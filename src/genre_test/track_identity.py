from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrackIdentity:
    track_id: str
    sha256: str
    size_bytes: int
    path: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def identify_track(path: Path) -> TrackIdentity:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    digest = sha256_file(resolved)
    return TrackIdentity(
        track_id=f"sha256:{digest}",
        sha256=digest,
        size_bytes=resolved.stat().st_size,
        path=str(resolved),
    )
