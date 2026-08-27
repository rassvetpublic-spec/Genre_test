from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def ensure_mert_weight_norm_compat(mert_dir: Path) -> dict[str, Any]:
    """Make the pinned legacy MERT checkpoint load correctly on modern PyTorch.

    PyTorch's modern weight_norm parametrization names the two tensors
    ``parametrizations.weight.original0/original1`` while the pinned MERT checkpoint
    stores the numerically identical tensors as ``weight_g/weight_v``. Older
    Transformers loading code does not reliably apply that key migration before
    reporting the modern tensors as newly initialized.

    This function rewrites only the two state-dict *keys*. Tensor values are copied
    byte-for-byte by torch and no numerical model parameter is altered.
    """

    import torch

    mert_dir = Path(mert_dir).resolve()
    checkpoint_path = mert_dir / "pytorch_model.bin"
    if not checkpoint_path.is_file():
        raise FileNotFoundError(checkpoint_path)

    sha_before = _sha256_file(checkpoint_path)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise RuntimeError("Pinned MERT checkpoint is not a plain state_dict mapping")

    migrated: list[dict[str, str]] = []
    verified: list[str] = []
    changed = False

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
            changed = True
            migrated.append({"from": legacy_key, "to": modern_key})
            verified.append(modern_key)
            continue

        if has_legacy:
            state[modern_key] = state.pop(legacy_key)
            changed = True
            migrated.append({"from": legacy_key, "to": modern_key})
            verified.append(modern_key)
            continue

        if has_modern:
            verified.append(modern_key)
            continue

        raise RuntimeError(
            "Pinned MERT checkpoint is missing both legacy and modern weight_norm key: "
            f"{legacy_key} / {modern_key}"
        )

    action = "already-compatible"
    if changed:
        temporary = checkpoint_path.with_suffix(".bin.genre-test-tmp")
        try:
            torch.save(state, temporary)
            os.replace(temporary, checkpoint_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        action = "patched"

    sha_after = _sha256_file(checkpoint_path)

    verify_state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    missing_modern = [
        key
        for key in LEGACY_TO_MODERN_WEIGHT_NORM_KEYS.values()
        if key not in verify_state
    ]
    remaining_legacy = [
        key for key in LEGACY_TO_MODERN_WEIGHT_NORM_KEYS if key in verify_state
    ]
    if missing_modern or remaining_legacy:
        raise RuntimeError(
            "MERT weight_norm compatibility verification failed: "
            f"missing_modern={missing_modern}, remaining_legacy={remaining_legacy}"
        )

    return {
        "status": "OK",
        "compat_version": MERT_WEIGHT_NORM_COMPAT_VERSION,
        "action": action,
        "checkpoint": str(checkpoint_path),
        "sha256_before": sha_before,
        "sha256_after": sha_after,
        "migrated_keys": migrated,
        "verified_modern_keys": verified,
        "numerical_weights_changed": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply/verify the Genre_test MERT modern-PyTorch weight_norm compatibility remap."
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
