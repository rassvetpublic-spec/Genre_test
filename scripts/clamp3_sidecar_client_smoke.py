from __future__ import annotations

import argparse
import json
import math
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

from genre_test.retrieval import Clamp3SidecarBackend  # noqa: E402


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def _norm(values: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genre_test core -> persistent CLaMP sidecar integration smoke"
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--audio", type=Path)
    parser.add_argument(
        "--text",
        default="мрачный электронный трек с мощными барабанами и напряжённой энергией",
    )
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")

    repo_root = args.repo_root.resolve()
    backend = Clamp3SidecarBackend.from_repo_defaults(
        repo_root,
        request_timeout_s=args.timeout,
    )
    report: dict[str, Any] = {
        "backend": backend.info.to_dict(),
        "backend_fingerprint": backend.info.fingerprint,
    }

    started = time.perf_counter()
    health = backend.health()
    report["health"] = {
        "status": health.status,
        "value": health.value,
        "details": health.details,
        "latency_seconds": time.perf_counter() - started,
    }
    if health.status not in {"OK", "WARN"}:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        backend.close()
        return 2

    try:
        text_vectors: list[tuple[float, ...]] = []
        text_latencies: list[float] = []
        for _ in range(args.repeat):
            started = time.perf_counter()
            vector = backend.embed_text(args.text, language="ru")
            text_latencies.append(time.perf_counter() - started)
            text_vectors.append(vector.values)
        report["text"] = {
            "query": args.text,
            "latency_seconds": text_latencies,
            "norm": _norm(text_vectors[0]),
            "repeat_cosine": (
                _cosine(text_vectors[0], text_vectors[-1]) if args.repeat > 1 else None
            ),
            "vector_head": list(text_vectors[0][:8]),
        }

        if args.audio is not None:
            audio_path = args.audio.resolve()
            if not audio_path.is_file():
                raise FileNotFoundError(audio_path)
            audio_vectors: list[tuple[float, ...]] = []
            audio_latencies: list[float] = []
            for _ in range(args.repeat):
                started = time.perf_counter()
                vector = backend.embed_audio(
                    audio_path,
                    track_id=f"sidecar-smoke:{audio_path.name}",
                )
                audio_latencies.append(time.perf_counter() - started)
                audio_vectors.append(vector.values)
            report["audio"] = {
                "path": str(audio_path),
                "latency_seconds": audio_latencies,
                "norm": _norm(audio_vectors[0]),
                "repeat_cosine": (
                    _cosine(audio_vectors[0], audio_vectors[-1]) if args.repeat > 1 else None
                ),
                "text_audio_cosine": _cosine(text_vectors[0], audio_vectors[0]),
                "vector_head": list(audio_vectors[0][:8]),
            }

        report["stderr_tail"] = list(backend.stderr_tail)
        report["status"] = "OK"
    finally:
        backend.close()

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out is not None:
        output = args.json_out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
