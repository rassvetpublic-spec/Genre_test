from .backend import RetrievalBackend
from .catalog import CatalogTrack, catalog_by_track_id, filter_track_ids, load_catalog_tracks
from .clamp3_sidecar_backend import (
    Clamp3SidecarBackend,
    Clamp3SidecarError,
    default_clamp3_backend_info,
)
from .contracts import (
    AudioEmbeddingRecord,
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalHealth,
    SearchFilter,
    SearchHit,
    SearchQuery,
    SegmentEmbeddingRecord,
    TextEmbeddingRecord,
)
from .export import write_search_csv, write_search_json
from .health import detect_retrieval_health
from .index import DenseCosineIndex, DenseIndexStats
from .service import (
    MAX_TEXT_QUERY_CHARS,
    CatalogSearchHit,
    IndexRunReport,
    IndexStatus,
    SearchResult,
    index_catalog,
    index_status,
    rebuild_catalog,
    search_audio,
    search_text,
)
from .sidecar_protocol import (
    PROTOCOL_VERSION,
    SidecarProtocolError,
    SidecarRequest,
    SidecarResponse,
    decode_vector_f32,
    encode_vector_f32,
)
from .storage import RetrievalStore, SearchQueryRecord, StoredEmbedding

__all__ = [
    "MAX_TEXT_QUERY_CHARS",
    "PROTOCOL_VERSION",
    "AudioEmbeddingRecord",
    "CatalogSearchHit",
    "CatalogTrack",
    "Clamp3SidecarBackend",
    "Clamp3SidecarError",
    "DenseCosineIndex",
    "DenseIndexStats",
    "EmbeddingIdentity",
    "EmbeddingVector",
    "IndexRunReport",
    "IndexStatus",
    "RetrievalBackend",
    "RetrievalBackendInfo",
    "RetrievalHealth",
    "RetrievalStore",
    "SearchFilter",
    "SearchHit",
    "SearchQuery",
    "SearchQueryRecord",
    "SearchResult",
    "SegmentEmbeddingRecord",
    "SidecarProtocolError",
    "SidecarRequest",
    "SidecarResponse",
    "StoredEmbedding",
    "TextEmbeddingRecord",
    "catalog_by_track_id",
    "decode_vector_f32",
    "default_clamp3_backend_info",
    "detect_retrieval_health",
    "encode_vector_f32",
    "filter_track_ids",
    "index_catalog",
    "index_status",
    "load_catalog_tracks",
    "rebuild_catalog",
    "search_audio",
    "search_text",
    "write_search_csv",
    "write_search_json",
]
