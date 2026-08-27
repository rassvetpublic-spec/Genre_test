from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
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


def _process_rss_bytes(pid: int | None) -> int | None:
    if pid is None:
        return None
    try:
        import psutil
    except ImportError:
        return None
    try:
        return int(psutil.Process(pid).memory_info().rss)
    except psutil.Error:
        return None


def _gpu_memory_mib(pid: int | None) -> int | None:
    if pid is None:
        return 0
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return None
    try:
        completed = subprocess.run(
            [
                nvidia_smi,
                "--query-compute-apps=pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=10.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    for raw in completed.stdout.splitlines():
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) < 2:
            continue
        try:
            row_pid = int(parts[0])
        except ValueError:
            continue
        if row_pid != pid:
            continue
        try:
            return int(float(parts[1]))
        except ValueError:
            return None
    return 0


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

    sidecar_pid = backend.process_id
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
        report["lifecycle"] = {
            "pid": sidecar_pid,
            "rss_bytes_before_close": _process_rss_bytes(sidecar_pid),
            "gpu_memory_mib_before_close": _gpu_memory_mib(sidecar_pid),
        }
    finally:
        backend.close()

    time.sleep(0.5)
    report.setdefault("lifecycle", {})
    report["lifecycle"].update(
        {
            "running_after_close": backend.is_running,
            "rss_bytes_after_close": _process_rss_bytes(sidecar_pid),
            "gpu_memory_mib_after_close": _gpu_memory_mib(sidecar_pid),
        }
    )

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
