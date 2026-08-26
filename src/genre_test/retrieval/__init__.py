from .backend import RetrievalBackend
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
from .health import detect_retrieval_health
from .index import DenseCosineIndex, DenseIndexStats
from .sidecar_protocol import (
    PROTOCOL_VERSION,
    SidecarProtocolError,
    SidecarRequest,
    SidecarResponse,
    decode_vector_f32,
    encode_vector_f32,
)
from .storage import RetrievalStore, StoredEmbedding

__all__ = [
    "PROTOCOL_VERSION",
    "AudioEmbeddingRecord",
    "Clamp3SidecarBackend",
    "Clamp3SidecarError",
    "DenseCosineIndex",
    "DenseIndexStats",
    "EmbeddingIdentity",
    "EmbeddingVector",
    "RetrievalBackend",
    "RetrievalBackendInfo",
    "RetrievalHealth",
    "RetrievalStore",
    "SearchFilter",
    "SearchHit",
    "SearchQuery",
    "SegmentEmbeddingRecord",
    "SidecarProtocolError",
    "SidecarRequest",
    "SidecarResponse",
    "StoredEmbedding",
    "TextEmbeddingRecord",
    "decode_vector_f32",
    "default_clamp3_backend_info",
    "detect_retrieval_health",
    "encode_vector_f32",
]
