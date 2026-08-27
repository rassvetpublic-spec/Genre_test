from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CLAMP3_CODE_REPO = "https://github.com/sanderwood/clamp3.git"
CLAMP3_CODE_REVISION = "9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8"

CLAMP3_WEIGHT_REPO = "sander-wood/clamp3"
CLAMP3_WEIGHT_REVISION = "791815a04a3a2bd9ab64cf590ba8307930c179e6"
CLAMP3_WEIGHT_VARIANT = "saas"
CLAMP3_WEIGHT_FILENAME = (
    "weights_clamp3_saas_h_size_768_t_model_FacebookAI_xlm-roberta-base_"
    "t_length_128_a_size_768_a_layers_12_a_length_128_s_size_768_"
    "s_layers_12_p_size_64_p_length_512.pth"
)
CLAMP3_WEIGHT_SHA256 = "5033f868e3977be3945ee416b5a1718d5589a173c7ba8982231d8c94a6441d80"
CLAMP3_WEIGHT_SIZE_BYTES = 2_571_027_658
CLAMP3_LICENSE = "MIT"

MERT_MODEL_ID = "m-a-p/MERT-v1-95M"
MERT_REVISION = "55fa29e5522049926c03d2ff9ae54d22c20e668f"
MERT_LICENSE = "CC-BY-NC-4.0"
MERT_WEIGHT_NORM_COMPAT = "mert-weight-norm-key-remap-v1"

TEXT_MODEL_ID = "FacebookAI/xlm-roberta-base"
TEXT_MODEL_REVISION = "e73636d4f797dec63c3081bb6ed5c7b0bb3f2089"
TEXT_MODEL_LICENSE = "MIT"

PREPROCESSING_VERSION = "clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3"
TARGET_SAMPLE_RATE = 24_000
RESAMPLER = "scipy.signal.resample_poly-1.13.1"
MONO = True
RAW_WAVEFORM_NORMALIZE = False
PROCESSOR_NORMALIZE = True
WINDOW_SECONDS = 5.0
WINDOW_OVERLAP_PERCENT = 0.0
MIN_FINAL_WINDOW_SECONDS = 1.0
MERT_LAYER = None
MERT_REDUCTION = "mean"
CLAMP3_AUDIO_MAX_LENGTH = 128
CLAMP3_TEXT_MAX_LENGTH = 128
EMBEDDING_DIMENSION = 768
NORMALIZATION = "l2"


def selected_model_manifest() -> dict[str, Any]:
    """Return the immutable model/preprocessing identity selected for the v0.5 P0 spike."""

    return {
        "clamp3": {
            "code_repo": CLAMP3_CODE_REPO,
            "code_revision": CLAMP3_CODE_REVISION,
            "weight_repo": CLAMP3_WEIGHT_REPO,
            "weight_revision": CLAMP3_WEIGHT_REVISION,
            "weight_variant": CLAMP3_WEIGHT_VARIANT,
            "weight_filename": CLAMP3_WEIGHT_FILENAME,
            "weight_sha256": CLAMP3_WEIGHT_SHA256,
            "weight_size_bytes": CLAMP3_WEIGHT_SIZE_BYTES,
            "license": CLAMP3_LICENSE,
        },
        "mert": {
            "model_id": MERT_MODEL_ID,
            "revision": MERT_REVISION,
            "license": MERT_LICENSE,
            "weight_norm_compat": MERT_WEIGHT_NORM_COMPAT,
        },
        "text": {
            "model_id": TEXT_MODEL_ID,
            "revision": TEXT_MODEL_REVISION,
            "license": TEXT_MODEL_LICENSE,
        },
        "preprocessing": {
            "version": PREPROCESSING_VERSION,
            "target_sample_rate": TARGET_SAMPLE_RATE,
            "resampler": RESAMPLER,
            "mono": MONO,
            "raw_waveform_normalize": RAW_WAVEFORM_NORMALIZE,
            "processor_normalize": PROCESSOR_NORMALIZE,
            "window_seconds": WINDOW_SECONDS,
            "window_overlap_percent": WINDOW_OVERLAP_PERCENT,
            "min_final_window_seconds": MIN_FINAL_WINDOW_SECONDS,
            "mert_layer": MERT_LAYER,
            "mert_reduction": MERT_REDUCTION,
            "clamp3_audio_max_length": CLAMP3_AUDIO_MAX_LENGTH,
            "clamp3_text_max_length": CLAMP3_TEXT_MAX_LENGTH,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "normalization": NORMALIZATION,
        },
    }


def manifest_fingerprint() -> str:
    payload = json.dumps(
        selected_model_manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def verify_clamp3_weight(path: str | Path) -> bool:
    candidate = Path(path)
    return (
        candidate.is_file()
        and candidate.stat().st_size == CLAMP3_WEIGHT_SIZE_BYTES
        and sha256_file(candidate) == CLAMP3_WEIGHT_SHA256
    )
