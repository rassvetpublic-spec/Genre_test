from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import time
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from genre_test.retrieval.model_pins import (  # noqa: E402
    CLAMP3_AUDIO_MAX_LENGTH,
    CLAMP3_CODE_REVISION,
    CLAMP3_TEXT_MAX_LENGTH,
    CLAMP3_WEIGHT_FILENAME,
    CLAMP3_WEIGHT_REPO,
    CLAMP3_WEIGHT_REVISION,
    EMBEDDING_DIMENSION,
    MERT_MODEL_ID,
    MERT_REVISION,
    MIN_FINAL_WINDOW_SECONDS,
    TARGET_SAMPLE_RATE,
    TEXT_MODEL_ID,
    TEXT_MODEL_REVISION,
    WINDOW_SECONDS,
    manifest_fingerprint,
    selected_model_manifest,
    verify_clamp3_weight,
)


def _default_runtime_root() -> Path:
    return REPO_ROOT / ".genre_test" / "retrieval"


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _runtime_versions() -> dict[str, str | None]:
    versions = {
        name: _package_version(name)
        for name in (
            "torch",
            "torchaudio",
            "transformers",
            "accelerate",
            "huggingface_hub",
            "numpy",
            "soundfile",
        )
    }
    versions["python"] = sys.version.split()[0]
    return versions


def _download_assets(runtime_root: Path) -> dict[str, Path]:
    from huggingface_hub import hf_hub_download, snapshot_download

    models_root = runtime_root / "models"
    models_root.mkdir(parents=True, exist_ok=True)

    clamp_dir = models_root / "clamp3-saas"
    clamp_dir.mkdir(parents=True, exist_ok=True)
    clamp_weight = Path(
        hf_hub_download(
            repo_id=CLAMP3_WEIGHT_REPO,
            filename=CLAMP3_WEIGHT_FILENAME,
            revision=CLAMP3_WEIGHT_REVISION,
            local_dir=clamp_dir,
        )
    )
    if not verify_clamp3_weight(clamp_weight):
        raise RuntimeError(
            "Downloaded CLaMP 3 SAAS weight failed size/SHA-256 verification: "
            f"{clamp_weight}"
        )

    mert_dir = models_root / "mert-v1-95m"
    snapshot_download(
        repo_id=MERT_MODEL_ID,
        revision=MERT_REVISION,
        local_dir=mert_dir,
        allow_patterns=[
            "config.json",
            "configuration_MERT.py",
            "modeling_MERT.py",
            "preprocessor_config.json",
            "pytorch_model.bin",
        ],
    )

    text_dir = models_root / "xlm-roberta-base"
    snapshot_download(
        repo_id=TEXT_MODEL_ID,
        revision=TEXT_MODEL_REVISION,
        local_dir=text_dir,
        allow_patterns=[
            "config.json",
            "model.safetensors",
            "pytorch_model.bin",
            "sentencepiece.bpe.model",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
        ],
    )

    return {
        "clamp_weight": clamp_weight,
        "mert_dir": mert_dir,
        "text_dir": text_dir,
    }


def _existing_assets(runtime_root: Path) -> dict[str, Path]:
    models_root = runtime_root / "models"
    clamp_weight = models_root / "clamp3-saas" / CLAMP3_WEIGHT_FILENAME
    mert_dir = models_root / "mert-v1-95m"
    text_dir = models_root / "xlm-roberta-base"

    if not verify_clamp3_weight(clamp_weight):
        raise FileNotFoundError(
            "Pinned CLaMP 3 SAAS weight is missing or corrupt. "
            "Run with --download-models first."
        )
    if not (mert_dir / "config.json").is_file():
        raise FileNotFoundError("Pinned MERT snapshot is missing. Run with --download-models first.")
    if not (text_dir / "config.json").is_file():
        raise FileNotFoundError(
            "Pinned XLM-R snapshot is missing. Run with --download-models first."
        )

    return {
        "clamp_weight": clamp_weight,
        "mert_dir": mert_dir,
        "text_dir": text_dir,
    }


def _load_clamp(runtime_root: Path, upstream_root: Path, assets: dict[str, Path]):
    import torch
    from transformers import AutoTokenizer, BertConfig

    code_dir = upstream_root / "code"
    if not code_dir.is_dir():
        raise FileNotFoundError(
            f"Pinned CLaMP source checkout not found at {code_dir}. "
            "Run scripts/setup_clamp3_runtime.ps1 -Install first."
        )
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

    from utils import CLaMP3Model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    audio_config = BertConfig(
        vocab_size=1,
        hidden_size=EMBEDDING_DIMENSION,
        num_hidden_layers=12,
        num_attention_heads=12,
        intermediate_size=EMBEDDING_DIMENSION * 4,
        max_position_embeddings=CLAMP3_AUDIO_MAX_LENGTH,
    )
    symbolic_config = BertConfig(
        vocab_size=1,
        hidden_size=EMBEDDING_DIMENSION,
        num_hidden_layers=12,
        num_attention_heads=12,
        intermediate_size=EMBEDDING_DIMENSION * 4,
        max_position_embeddings=512,
    )
    model = CLaMP3Model(
        audio_config=audio_config,
        symbolic_config=symbolic_config,
        text_model_name=str(assets["text_dir"]),
        hidden_size=EMBEDDING_DIMENSION,
        load_m3=False,
    ).to(device)
    model.eval()

    checkpoint = torch.load(
        assets["clamp_weight"], map_location="cpu", weights_only=True
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    tokenizer = AutoTokenizer.from_pretrained(str(assets["text_dir"]), local_files_only=True)

    return model, tokenizer, device, checkpoint


def _weighted_global(features: list[Any], weights: list[int]):
    import torch

    stacked = torch.cat(features, dim=0)
    weight_tensor = torch.tensor(weights, device=stacked.device, dtype=stacked.dtype).view(-1, 1)
    result = (stacked * weight_tensor).sum(dim=0) / weight_tensor.sum()
    return torch.nn.functional.normalize(result.reshape(-1), p=2, dim=0)


def _text_embedding(model, tokenizer, text: str, device):
    import torch

    input_ids = tokenizer(text, return_tensors="pt")["input_ids"].squeeze(0)
    if input_ids.numel() == 0:
        raise ValueError("Text query produced zero tokens")

    segments = [
        input_ids[start : start + CLAMP3_TEXT_MAX_LENGTH]
        for start in range(0, input_ids.numel(), CLAMP3_TEXT_MAX_LENGTH)
    ]
    if input_ids.numel() > CLAMP3_TEXT_MAX_LENGTH:
        segments[-1] = input_ids[-CLAMP3_TEXT_MAX_LENGTH:]

    outputs: list[Any] = []
    weights: list[int] = []
    with torch.no_grad():
        for segment in segments:
            actual = int(segment.numel())
            mask = torch.cat(
                (
                    torch.ones(actual),
                    torch.zeros(CLAMP3_TEXT_MAX_LENGTH - actual),
                )
            )
            padding = torch.full(
                (CLAMP3_TEXT_MAX_LENGTH - actual,), tokenizer.pad_token_id, dtype=torch.long
            )
            padded = torch.cat((segment, padding), dim=0)
            output = model.get_text_features(
                text_inputs=padded.unsqueeze(0).to(device),
                text_masks=mask.unsqueeze(0).to(device),
                get_global=True,
            )
            outputs.append(output)
            weights.append(actual)
    return _weighted_global(outputs, weights)


def _mert_features(audio_path: Path, upstream_root: Path, mert_dir: Path, device):
    import torch

    audio_preprocess_dir = upstream_root / "preprocessing" / "audio"
    if str(audio_preprocess_dir) not in sys.path:
        sys.path.insert(0, str(audio_preprocess_dir))

    from hf_pretrains import HuBERTFeature
    from MERT_utils import load_audio

    extractor = HuBERTFeature(
        str(mert_dir),
        TARGET_SAMPLE_RATE,
        force_half=False,
        processor_normalize=True,
    ).to(device)
    extractor.eval()

    waveform = load_audio(
        str(audio_path),
        target_sr=TARGET_SAMPLE_RATE,
        is_mono=True,
        is_normalize=False,
        crop_to_length_in_sec=None,
        crop_randomly=False,
        device=device,
    )
    processed = extractor.process_wav(waveform).to(device)
    window_samples = int(TARGET_SAMPLE_RATE * WINDOW_SECONDS)
    min_final_samples = int(TARGET_SAMPLE_RATE * MIN_FINAL_WINDOW_SECONDS)

    chunks = [
        processed[:, start : start + window_samples]
        for start in range(0, processed.shape[-1], window_samples)
    ]
    if chunks and chunks[-1].shape[-1] < min_final_samples:
        chunks = chunks[:-1]
    if not chunks:
        raise ValueError("Audio is too short for the selected CLaMP/MERT preprocessing policy")

    chunk_features: list[Any] = []
    with torch.no_grad():
        for chunk in chunks:
            chunk_features.append(extractor(chunk, layer=None, reduction="mean"))
    features = torch.cat(chunk_features, dim=1)
    return features.mean(dim=0, keepdim=True).reshape(-1, EMBEDDING_DIMENSION)


def _audio_embedding(model, mert_features, device):
    import torch

    zero = torch.zeros((1, EMBEDDING_DIMENSION), dtype=mert_features.dtype)
    input_data = torch.cat((zero, mert_features.cpu(), zero), dim=0)
    segments = [
        input_data[start : start + CLAMP3_AUDIO_MAX_LENGTH]
        for start in range(0, input_data.shape[0], CLAMP3_AUDIO_MAX_LENGTH)
    ]
    if input_data.shape[0] > CLAMP3_AUDIO_MAX_LENGTH:
        segments[-1] = input_data[-CLAMP3_AUDIO_MAX_LENGTH:]

    outputs: list[Any] = []
    weights: list[int] = []
    with torch.no_grad():
        for segment in segments:
            actual = int(segment.shape[0])
            mask = torch.cat(
                (
                    torch.ones(actual),
                    torch.zeros(CLAMP3_AUDIO_MAX_LENGTH - actual),
                )
            )
            padding = torch.zeros(
                (CLAMP3_AUDIO_MAX_LENGTH - actual, EMBEDDING_DIMENSION),
                dtype=segment.dtype,
            )
            padded = torch.cat((segment, padding), dim=0)
            output = model.get_audio_features(
                audio_inputs=padded.unsqueeze(0).to(device),
                audio_masks=mask.unsqueeze(0).to(device),
                get_global=True,
            )
            outputs.append(output)
            weights.append(actual)
    return _weighted_global(outputs, weights)


def _cosine(left, right) -> float:
    import torch

    return float(torch.dot(left.reshape(-1), right.reshape(-1)).item())


def _run_smoke(
    runtime_root: Path,
    upstream_root: Path,
    assets: dict[str, Path],
    text: str,
    audio_path: Path | None,
    repeat: int,
) -> dict[str, Any]:
    import torch

    if repeat < 1:
        raise ValueError("--repeat must be >= 1")

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    load_started = time.perf_counter()
    model, tokenizer, device, checkpoint = _load_clamp(runtime_root, upstream_root, assets)
    load_seconds = time.perf_counter() - load_started

    text_vectors = []
    text_latencies = []
    for _ in range(repeat):
        started = time.perf_counter()
        text_vectors.append(_text_embedding(model, tokenizer, text, device).detach().cpu())
        text_latencies.append(time.perf_counter() - started)

    report: dict[str, Any] = {
        "status": "OK",
        "manifest_fingerprint": manifest_fingerprint(),
        "clamp3_code_revision": CLAMP3_CODE_REVISION,
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_min_eval_loss": checkpoint.get("min_eval_loss"),
        "device": str(device),
        "runtime_versions": _runtime_versions(),
        "model_load_seconds": load_seconds,
        "text": {
            "query": text,
            "repeat": repeat,
            "latency_seconds": text_latencies,
            "norm": float(text_vectors[0].norm().item()),
            "repeat_cosine": (
                _cosine(text_vectors[0], text_vectors[-1]) if repeat > 1 else None
            ),
            "vector_head": text_vectors[0][:8].tolist(),
        },
    }

    if audio_path is not None:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        audio_vectors = []
        audio_latencies = []
        mert_latencies = []
        for _ in range(repeat):
            started = time.perf_counter()
            mert_started = time.perf_counter()
            features = _mert_features(audio_path, upstream_root, assets["mert_dir"], device)
            mert_latencies.append(time.perf_counter() - mert_started)
            audio_vectors.append(_audio_embedding(model, features, device).detach().cpu())
            audio_latencies.append(time.perf_counter() - started)
        report["audio"] = {
            "path": str(audio_path),
            "repeat": repeat,
            "mert_latency_seconds": mert_latencies,
            "total_latency_seconds": audio_latencies,
            "norm": float(audio_vectors[0].norm().item()),
            "repeat_cosine": (
                _cosine(audio_vectors[0], audio_vectors[-1]) if repeat > 1 else None
            ),
            "text_audio_cosine": _cosine(text_vectors[0], audio_vectors[0]),
            "vector_head": audio_vectors[0][:8].tolist(),
        }

    if torch.cuda.is_available():
        report["cuda"] = {
            "device_name": torch.cuda.get_device_name(0),
            "allocated_bytes": int(torch.cuda.memory_allocated()),
            "reserved_bytes": int(torch.cuda.memory_reserved()),
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        }
    else:
        report["cuda"] = None

    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pinned real CLaMP 3 SAAS + MERT runtime/download/smoke gate."
    )
    parser.add_argument("--runtime-root", type=Path, default=_default_runtime_root())
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--download-models", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--audio", type=Path)
    parser.add_argument(
        "--text",
        default="мрачный электронный трек с мощными барабанами и напряжённой энергией",
    )
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    runtime_root = args.runtime_root.resolve()
    upstream_root = (
        args.upstream_root.resolve()
        if args.upstream_root
        else runtime_root / "upstream" / "clamp3"
    )

    if args.manifest:
        payload = {
            "manifest": selected_model_manifest(),
            "manifest_fingerprint": manifest_fingerprint(),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    assets = (
        _download_assets(runtime_root)
        if args.download_models
        else _existing_assets(runtime_root)
    )
    report = _run_smoke(
        runtime_root=runtime_root,
        upstream_root=upstream_root,
        assets=assets,
        text=args.text,
        audio_path=args.audio.resolve() if args.audio else None,
        repeat=args.repeat,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
