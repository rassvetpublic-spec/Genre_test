from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contracts import EmbeddingVector, SearchHit
from .storage import RetrievalStore


@dataclass(frozen=True)
class DenseIndexStats:
    tracks: int
    dimension: int
    backend_fingerprint: str


class DenseCosineIndex:
    """Exact dense cosine index for the current ~10k-track catalog."""

    def __init__(
        self,
        *,
        backend_fingerprint: str,
        track_ids: tuple[str, ...],
        paths: tuple[str, ...],
        matrix: np.ndarray,
    ) -> None:
        if matrix.ndim != 2:
            raise ValueError("matrix must be 2-dimensional")
        if matrix.shape[0] != len(track_ids) or len(track_ids) != len(paths):
            raise ValueError("track_ids, paths and matrix rows must have equal length")
        if matrix.shape[0] == 0:
            raise ValueError("index must contain at least one track")
        if matrix.shape[1] == 0:
            raise ValueError("embedding dimension must be positive")
        if matrix.dtype != np.float32:
            matrix = matrix.astype(np.float32, copy=False)
        norms = np.linalg.norm(matrix, axis=1)
        if not np.allclose(norms, 1.0, rtol=1e-4, atol=1e-4):
            raise ValueError("index rows must be L2 normalized")

        self.backend_fingerprint = backend_fingerprint
        self.track_ids = track_ids
        self.paths = paths
        self.matrix = np.ascontiguousarray(matrix)

    @classmethod
    def from_store(
        cls,
        store: RetrievalStore,
        *,
        backend_fingerprint: str,
    ) -> DenseCosineIndex:
        records = store.iter_audio(
            backend_fingerprint=backend_fingerprint,
            scope="full",
        )
        if not records:
            raise ValueError("no full-track embeddings available for backend")

        track_ids: list[str] = []
        paths: list[str] = []
        vectors: list[tuple[float, ...]] = []
        dimension: int | None = None

        for record in records:
            track_id = record.identity.track_id
            if track_id is None:
                continue
            if record.path is None:
                raise ValueError(f"audio embedding {record.cache_key} has no path")
            if dimension is None:
                dimension = record.vector.dimension
            elif record.vector.dimension != dimension:
                raise ValueError("mixed embedding dimensions in one backend index")
            track_ids.append(track_id)
            paths.append(record.path)
            vectors.append(record.vector.values)

        if not vectors:
            raise ValueError("no usable full-track embeddings available for backend")

        matrix = np.asarray(vectors, dtype=np.float32)
        return cls(
            backend_fingerprint=backend_fingerprint,
            track_ids=tuple(track_ids),
            paths=tuple(paths),
            matrix=matrix,
        )

    @property
    def stats(self) -> DenseIndexStats:
        return DenseIndexStats(
            tracks=self.matrix.shape[0],
            dimension=self.matrix.shape[1],
            backend_fingerprint=self.backend_fingerprint,
        )

    def search(
        self,
        query: EmbeddingVector,
        *,
        top_k: int = 20,
        exclude_track_id: str | None = None,
        allowed_track_ids: set[str] | None = None,
    ) -> list[SearchHit]:
        if query.identity.backend_fingerprint != self.backend_fingerprint:
            raise ValueError("query backend fingerprint does not match index")
        if query.dimension != self.matrix.shape[1]:
            raise ValueError(
                f"query dimension mismatch: expected {self.matrix.shape[1]}, "
                f"got {query.dimension}"
            )
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_values = np.asarray(query.values, dtype=np.float32)
        similarities = self.matrix @ query_values

        # Do not rely on SQLite row order or an unstable numeric sort for equal scores.
        # The explicit secondary keys make ranking reproducible across runs/platforms.
        candidates = sorted(
            range(len(self.track_ids)),
            key=lambda row_index: (
                -float(similarities[row_index]),
                self.track_ids[row_index],
                self.paths[row_index],
            ),
        )
        hits: list[SearchHit] = []
        for row_index in candidates:
            track_id = self.track_ids[row_index]
            if exclude_track_id is not None and track_id == exclude_track_id:
                continue
            if allowed_track_ids is not None and track_id not in allowed_track_ids:
                continue
            hits.append(
                SearchHit(
                    rank=len(hits) + 1,
                    track_id=track_id,
                    path=self.paths[row_index],
                    similarity=float(similarities[row_index]),
                    backend_fingerprint=self.backend_fingerprint,
                )
            )
            if len(hits) >= top_k:
                break
        return hits
