"""CLI for backend-neutral source/candidate technical comparison."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .mastering_metrics import CODEC_SPECS, compare_mastering_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genre-test-mastering-qc",
        description=(
            "Compare a reference WAV with a derived repair/master candidate using "
            "transient-retention, mono-loss and optional decoded-codec peak guards."
        ),
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, help="Write complete JSON result to this path")
    parser.add_argument(
        "--codec",
        action="append",
        choices=sorted(CODEC_SPECS),
        default=[],
        help="Run a real encode/decode codec preview; may be repeated",
    )
    parser.add_argument("--target-dbtp", type=float, default=None)
    parser.add_argument("--codec-safety-margin-db", type=float, default=0.1)
    parser.add_argument("--max-lag-seconds", type=float, default=2.0)
    parser.add_argument("--max-events", type=int, default=64)
    parser.add_argument("--attack-warn-db", type=float, default=-0.75)
    parser.add_argument("--attack-fail-db", type=float, default=-1.5)
    parser.add_argument("--mono-warn-db", type=float, default=-0.5)
    parser.add_argument("--mono-fail-db", type=float, default=-1.5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = compare_mastering_files(
        args.reference,
        args.candidate,
        codecs=args.codec,
        target_dbtp=args.target_dbtp,
        codec_safety_margin_db=args.codec_safety_margin_db,
        max_lag_seconds=args.max_lag_seconds,
        max_events=args.max_events,
        attack_warn_db=args.attack_warn_db,
        attack_fail_db=args.attack_fail_db,
        mono_warn_db=args.mono_warn_db,
        mono_fail_db=args.mono_fail_db,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result["overall_status"] != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
