from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MERT_WEIGHT_NORM_COMPAT_VERSION = "mert-weight-norm-key-remap-v1"

LEGACY_TO_MODERN_WEIGHT_NORM_KEYS = {
    "encoder.pos_conv_embed.conv.weight_g": (
        "encoder.pos_conv_embed.conv.parametrizations.weight.original0"
    ),
    "encoder.pos_conv_embed.conv.weight_v": (
        "encoder.pos_conv_embed.conv.parametrizations.weight.original1"
    ),
}


def _sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_mert_compatible_state_dict(mert_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the pinned MERT checkpoint with a key-only weight_norm remap in memory.

    Modern PyTorch represents weight_norm tensors as
    ``parametrizations.weight.original0/original1`` while the pinned MERT checkpoint
    stores the numerically identical tensors as ``weight_g/weight_v``. The original
    HuggingFace snapshot is never modified on disk; only the in-memory state-dict
    keys are remapped before ``MusicHubertModel.from_pretrained`` consumes them.
    """

    import torch

    mert_dir = Path(mert_dir).resolve()
    checkpoint_path = mert_dir / "pytorch_model.bin"
    if not checkpoint_path.is_file():
        raise FileNotFoundError(checkpoint_path)

    source_sha256 = _sha256_file(checkpoint_path)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise TypeError("Pinned MERT checkpoint is not a plain state_dict mapping")

    remapped: list[dict[str, str]] = []
    verified: list[str] = []

    for legacy_key, modern_key in LEGACY_TO_MODERN_WEIGHT_NORM_KEYS.items():
        has_legacy = legacy_key in state
        has_modern = modern_key in state

        if has_legacy and has_modern:
            if not torch.equal(state[legacy_key], state[modern_key]):
                raise RuntimeError(
                    "MERT checkpoint contains conflicting legacy/modern weight_norm tensors: "
                    f"{legacy_key} vs {modern_key}"
                )
            del state[legacy_key]
            remapped.append({"from": legacy_key, "to": modern_key})
            verified.append(modern_key)
            continue

        if has_legacy:
            state[modern_key] = state.pop(legacy_key)
            remapped.append({"from": legacy_key, "to": modern_key})
            verified.append(modern_key)
            continue

        if has_modern:
            verified.append(modern_key)
            continue

        raise RuntimeError(
            "Pinned MERT checkpoint is missing both legacy and modern weight_norm key: "
            f"{legacy_key} / {modern_key}"
        )

    missing_modern = [
        key
        for key in LEGACY_TO_MODERN_WEIGHT_NORM_KEYS.values()
        if key not in state
    ]
    remaining_legacy = [
        key for key in LEGACY_TO_MODERN_WEIGHT_NORM_KEYS if key in state
    ]
    if missing_modern or remaining_legacy:
        raise RuntimeError(
            "MERT weight_norm compatibility verification failed: "
            f"missing_modern={missing_modern}, remaining_legacy={remaining_legacy}"
        )

    report = {
        "status": "OK",
        "compat_version": MERT_WEIGHT_NORM_COMPAT_VERSION,
        "action": "in-memory-remap" if remapped else "already-modern",
        "checkpoint": str(checkpoint_path),
        "source_sha256": source_sha256,
        "remapped_keys": remapped,
        "verified_modern_keys": verified,
        "numerical_weights_changed": False,
        "source_checkpoint_modified": False,
    }
    return state, report


def ensure_mert_weight_norm_compat(mert_dir: Path) -> dict[str, Any]:
    """Validate that the pinned MERT checkpoint can be remapped without mutation."""

    _, report = load_mert_compatible_state_dict(mert_dir)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Genre_test MERT modern-PyTorch weight_norm compatibility."
    )
    parser.add_argument("--mert-dir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = ensure_mert_weight_norm_compat(args.mert_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out is not None:
        output = args.json_out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
