from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()


def _run(command: list[str], *, cwd: Path, timeout_s: float) -> dict[str, Any]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
        env=env,
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


def _new_analysis_json(log_dir: Path, before: set[Path]) -> Path:
    after = {path.resolve() for path in log_dir.glob("*.genre.*.json")}
    candidates = sorted(after - before)
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one new core analysis JSON under {log_dir}, found {len(candidates)}"
        )
    return candidates[0]


def _uses_cuda(value: Any) -> bool:
    return "cuda" in str(value or "").lower()


def _head_close(left: Any, right: Any, *, tolerance: float = 1e-5) -> bool:
    try:
        left_values = [float(value) for value in left]
        right_values = [float(value) for value in right]
    except (TypeError, ValueError):
        return False
    if not left_values or len(left_values) != len(right_values):
        return False
    return max(abs(a - b) for a, b in zip(left_values, right_values, strict=True)) <= tolerance


def _contains_newly_initialized(value: Any) -> bool:
    if isinstance(value, str):
        return "newly initialized" in value.lower()
    if isinstance(value, (list, tuple)):
        return any(_contains_newly_initialized(item) for item in value)
    return False


def _loading_info_clean(compat: Any) -> bool:
    if not isinstance(compat, dict):
        return False
    info = compat.get("loading_info")
    if not isinstance(info, dict):
        return False
    return not any(
        info.get(name)
        for name in ("missing_keys", "unexpected_keys", "mismatched_keys")
    )


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

    state_root = repo_root / ".genre_test"
    legacy_retrieval_root = state_root / "retrieval"
    core_python = repo_root / ".venv" / "Scripts" / "python.exe"
    core_cli = repo_root / ".venv" / "Scripts" / "genre-test.exe"
    isolated_python = (
        state_root
        / "runtimes"
        / "clamp3"
        / ".venv"
        / "Scripts"
        / "python.exe"
    )
    upstream_root = state_root / "upstream" / "clamp3"
    models_root = state_root / "models"
    mert_dir = models_root / "mert-v1-95m"
    log_dir = state_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")

    if legacy_retrieval_root.exists():
        raise RuntimeError(
            "Obsolete .genre_test/retrieval layout still exists. "
            "Run Genre_test_START.cmd retrieval-setup once to migrate it before P0."
        )

    for required in (core_python, core_cli, isolated_python):
        if not required.is_file():
            raise FileNotFoundError(required)
    if not models_root.is_dir():
        raise FileNotFoundError(models_root)
    if not mert_dir.is_dir():
        raise FileNotFoundError(mert_dir)
    if not (upstream_root / ".git").is_dir():
        raise FileNotFoundError(upstream_root / ".git")

    report: dict[str, Any] = {
        "status": "RUNNING",
        "audio": str(audio),
        "repeat": args.repeat,
        "state_root": str(state_root),
        "log_dir": str(log_dir),
        "gate": "CLAMP3_P0_27_29",
    }

    # Gate A: prove both MAEST and AudioSet AST actually exercised CUDA first.
    before_core = {path.resolve() for path in log_dir.glob("*.genre.*.json")}
    core_result = _run(
        [
            str(core_cli),
            "analyze",
            str(audio),
            "--out",
            str(log_dir),
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
    generated_core_path = _new_analysis_json(log_dir, before_core)
    core_analysis = _load_json(generated_core_path)
    core_analysis_path = log_dir / f"clamp3_p0_core_{stamp}.json"
    generated_core_path.replace(core_analysis_path)
    report["core_analysis"] = core_analysis
    report["artifacts"] = {"core": str(core_analysis_path)}

    semantic = core_analysis.get("semantic_evidence") or {}
    core_checks = {
        "maest_cuda": _uses_cuda(core_analysis.get("device")),
        "maest_windows_positive": int(core_analysis.get("windows_analyzed") or 0) > 0,
        "ast_present": bool(semantic),
        "ast_status_ok": str(semantic.get("status") or "").lower() == "ok",
        "ast_cuda": _uses_cuda(semantic.get("device")),
        "ast_windows_positive": int(semantic.get("windows_analyzed") or 0) > 0,
    }
    report["core_cuda_checks"] = core_checks
    if not all(core_checks.values()):
        raise RuntimeError(
            "Core CUDA precondition failed: the WAV must produce real MAEST + AudioSet AST CUDA evidence. "
            f"Checks: {core_checks}"
        )

    # Gate B: validate that the pinned MERT checkpoint can be translated from the
    # legacy weight_g/weight_v names to modern parametrization names in memory.
    # The source HuggingFace snapshot must remain byte-for-byte untouched.
    mert_compat_json = log_dir / f"clamp3_p0_mert_compat_{stamp}.json"
    mert_compat_result = _run(
        [
            str(isolated_python),
            str(repo_root / "scripts" / "clamp3_mert_compat.py"),
            "--mert-dir",
            str(mert_dir),
            "--json-out",
            str(mert_compat_json),
        ],
        cwd=repo_root,
        timeout_s=args.timeout,
    )
    report["mert_compat_command"] = mert_compat_result
    _require_ok("MERT weight_norm compatibility", mert_compat_result)
    report["mert_compat"] = _load_json(mert_compat_json)
    report["artifacts"]["mert_compat"] = str(mert_compat_json)

    direct_json = log_dir / f"clamp3_p0_direct_{stamp}.json"
    direct_result = _run(
        [
            str(isolated_python),
            str(repo_root / "scripts" / "clamp3_runtime_smoke.py"),
            "--runtime-root",
            str(state_root),
            "--upstream-root",
            str(upstream_root),
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
    report["artifacts"]["direct"] = str(direct_json)

    sidecar_json = log_dir / f"clamp3_p0_sidecar_{stamp}.json"
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
    report["artifacts"]["sidecar"] = str(sidecar_json)

    direct = report["direct_runtime"]
    sidecar = report["sidecar"]
    compat = report["mert_compat"]
    direct_mert_compat = direct.get("audio", {}).get("mert_compat") or {}
    direct_text_audio = float(direct["audio"]["text_audio_cosine"])
    sidecar_text_audio = float(sidecar["audio"]["text_audio_cosine"])
    sidecar_metrics = sidecar.get("runtime_metrics_before_close") or {}
    sidecar_cuda_metrics = sidecar_metrics.get("cuda") or {}
    sidecar_mert_compat = sidecar_metrics.get("mert_compat") or {}
    lifecycle = sidecar.get("lifecycle", {})

    checks = {
        **core_checks,
        "flat_state_layout": not legacy_retrieval_root.exists(),
        "mert_compat_status_ok": compat.get("status") == "OK",
        "mert_compat_numerical_weights_unchanged": (
            compat.get("numerical_weights_changed") is False
        ),
        "mert_source_checkpoint_unmodified": (
            compat.get("source_checkpoint_modified") is False
        ),
        "mert_compat_modern_keys_verified": len(compat.get("verified_modern_keys") or []) == 2,
        "direct_status_ok": direct.get("status") == "OK",
        "sidecar_status_ok": sidecar.get("status") == "OK",
        "direct_mert_compat_ok": direct_mert_compat.get("status") == "OK",
        "direct_mert_loading_exact": _loading_info_clean(direct_mert_compat),
        "direct_mert_no_newly_initialized": not _contains_newly_initialized(
            report["direct_runtime_command"].get("stderr")
        ),
        "sidecar_mert_no_newly_initialized": not _contains_newly_initialized(
            sidecar.get("stderr_tail")
        ),
        "direct_text_repeatable": float(direct["text"]["repeat_cosine"]) >= 0.99999,
        "direct_audio_repeatable": float(direct["audio"]["repeat_cosine"]) >= 0.99999,
        "sidecar_text_repeatable": float(sidecar["text"]["repeat_cosine"]) >= 0.99999,
        "sidecar_audio_repeatable": float(sidecar["audio"]["repeat_cosine"]) >= 0.99999,
        "direct_text_norm": abs(float(direct["text"]["norm"]) - 1.0) <= 1e-5,
        "direct_audio_norm": abs(float(direct["audio"]["norm"]) - 1.0) <= 1e-5,
        "sidecar_text_norm": abs(float(sidecar["text"]["norm"]) - 1.0) <= 1e-5,
        "sidecar_audio_norm": abs(float(sidecar["audio"]["norm"]) - 1.0) <= 1e-5,
        # Cross-process equality is part of P0: direct and persistent-sidecar paths
        # must represent the same input with the same pinned model/preprocessing.
        "cross_text_head_match": _head_close(
            direct["text"]["vector_head"], sidecar["text"]["vector_head"]
        ),
        "cross_audio_head_match": _head_close(
            direct["audio"]["vector_head"], sidecar["audio"]["vector_head"]
        ),
        "cross_text_audio_cosine_match": abs(direct_text_audio - sidecar_text_audio) <= 1e-5,
        "sidecar_mert_compat_ok": sidecar_mert_compat.get("status") == "OK",
        "sidecar_mert_loading_exact": _loading_info_clean(sidecar_mert_compat),
        "sidecar_ram_measured_before_close": int(sidecar_metrics.get("rss_bytes") or 0) > 0,
        "sidecar_cuda_allocated_before_close": (
            int(sidecar_cuda_metrics.get("allocated_bytes") or 0) > 0
        ),
        "sidecar_cuda_peak_measured": (
            int(sidecar_cuda_metrics.get("peak_allocated_bytes") or 0) > 0
        ),
        "sidecar_shutdown": lifecycle.get("running_after_close") is False,
        # Windows/WDDM can omit the process from nvidia-smi even while torch reports
        # live CUDA allocations. Release proof therefore requires both authoritative
        # in-process allocation before close and process termination after close.
        "sidecar_vram_released": (
            int(sidecar_cuda_metrics.get("allocated_bytes") or 0) > 0
            and lifecycle.get("running_after_close") is False
            and lifecycle.get("gpu_memory_mib_after_close") in {0, None}
        ),
    }
    report["checks"] = checks
    report["status"] = "PASS" if all(checks.values()) else "FAIL"

    final_path = (
        args.json_out.resolve()
        if args.json_out
        else log_dir / f"clamp3_p0_gate_{stamp}.json"
    )
    final_path.parent.mkdir(parents=True, exist_ok=True)
    report["artifacts"]["gate"] = str(final_path)
    final_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"P0 log: {final_path}")
    return 0 if report["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
