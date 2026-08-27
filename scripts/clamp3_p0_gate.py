from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()


def _run(command: list[str], *, cwd: Path, timeout_s: float) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_seconds": time.perf_counter() - started,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _require_ok(step: str, result: dict[str, Any]) -> None:
    if result["returncode"] != 0:
        raise RuntimeError(
            f"{step} failed with exit code {result['returncode']}\n"
            f"stdout:\n{result['stdout']}\n"
            f"stderr:\n{result['stderr']}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the complete Genre_test v0.5 CLaMP 3 #27/#29 hardware P0 gate."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.repeat < 2:
        raise SystemExit("--repeat must be >= 2 for the P0 repeatability gate")

    repo_root = args.repo_root.resolve()
    audio = args.audio.resolve()
    if not audio.is_file():
        raise FileNotFoundError(audio)

    core_python = repo_root / ".venv" / "Scripts" / "python.exe"
    core_cli = repo_root / ".venv" / "Scripts" / "genre-test.exe"
    isolated_python = (
        repo_root
        / ".genre_test"
        / "retrieval"
        / "runtime"
        / ".venv"
        / "Scripts"
        / "python.exe"
    )
    runtime_root = repo_root / ".genre_test" / "retrieval"
    evidence_root = runtime_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = evidence_root / f"p0_gate_{stamp}"
    session_dir.mkdir(parents=True, exist_ok=False)

    for required in (core_python, core_cli, isolated_python):
        if not required.is_file():
            raise FileNotFoundError(required)

    report: dict[str, Any] = {
        "status": "RUNNING",
        "audio": str(audio),
        "repeat": args.repeat,
        "session_dir": str(session_dir),
        "gate": "CLAMP3_P0_27_29",
    }

    # Gate A: prove MAEST + AudioSet AST have exercised CUDA before retrieval.
    core_out = session_dir / "core_cuda_probe"
    core_result = _run(
        [
            str(core_cli),
            "analyze",
            str(audio),
            "--out",
            str(core_out),
            "--device",
            "cuda",
            "--mode",
            "fast",
            "--semantic",
            "on",
            "--view",
            "normal",
            "--no-history",
        ],
        cwd=repo_root,
        timeout_s=args.timeout,
    )
    report["core_cuda_probe"] = core_result
    _require_ok("MAEST+AST CUDA probe", core_result)

    direct_json = session_dir / "direct_runtime.json"
    direct_result = _run(
        [
            str(isolated_python),
            str(repo_root / "scripts" / "clamp3_runtime_smoke.py"),
            "--runtime-root",
            str(runtime_root),
            "--audio",
            str(audio),
            "--repeat",
            str(args.repeat),
            "--json-out",
            str(direct_json),
        ],
        cwd=repo_root,
        timeout_s=args.timeout,
    )
    report["direct_runtime_command"] = direct_result
    _require_ok("direct isolated-runtime smoke", direct_result)
    report["direct_runtime"] = _load_json(direct_json)

    sidecar_json = session_dir / "sidecar.json"
    sidecar_result = _run(
        [
            str(core_python),
            str(repo_root / "scripts" / "clamp3_sidecar_client_smoke.py"),
            "--repo-root",
            str(repo_root),
            "--audio",
            str(audio),
            "--repeat",
            str(args.repeat),
            "--timeout",
            str(args.timeout),
            "--json-out",
            str(sidecar_json),
        ],
        cwd=repo_root,
        timeout_s=args.timeout,
    )
    report["sidecar_command"] = sidecar_result
    _require_ok("core -> persistent sidecar smoke", sidecar_result)
    report["sidecar"] = _load_json(sidecar_json)

    direct = report["direct_runtime"]
    sidecar = report["sidecar"]
    checks = {
        "direct_status_ok": direct.get("status") == "OK",
        "sidecar_status_ok": sidecar.get("status") == "OK",
        "direct_text_repeatable": float(direct["text"]["repeat_cosine"]) >= 0.99999,
        "direct_audio_repeatable": float(direct["audio"]["repeat_cosine"]) >= 0.99999,
        "sidecar_text_repeatable": float(sidecar["text"]["repeat_cosine"]) >= 0.99999,
        "sidecar_audio_repeatable": float(sidecar["audio"]["repeat_cosine"]) >= 0.99999,
        "direct_text_norm": abs(float(direct["text"]["norm"]) - 1.0) <= 1e-5,
        "direct_audio_norm": abs(float(direct["audio"]["norm"]) - 1.0) <= 1e-5,
        "sidecar_text_norm": abs(float(sidecar["text"]["norm"]) - 1.0) <= 1e-5,
        "sidecar_audio_norm": abs(float(sidecar["audio"]["norm"]) - 1.0) <= 1e-5,
        "sidecar_shutdown": sidecar.get("lifecycle", {}).get("running_after_close") is False,
        "sidecar_vram_released": sidecar.get("lifecycle", {}).get("gpu_memory_mib_after_close", 0) == 0,
    }
    report["checks"] = checks
    report["status"] = "PASS" if all(checks.values()) else "FAIL"

    final_path = args.json_out.resolve() if args.json_out else session_dir / "p0_gate.json"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"P0 evidence: {final_path}")
    return 0 if report["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
