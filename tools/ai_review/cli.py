from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import load_settings
from .errors import AIReviewError
from .orchestrator import ConsultOrchestrator
from .providers.factory import build_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ai_review",
        description="Local configurable cross-model consultation.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to JSON-compatible config.yaml.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    consult = subparsers.add_parser("consult", help="Run one independent cross-model consult.")
    consult.add_argument("--task", required=True, help="Task or question to consult on.")
    consult.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write the local run artifact.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings(args.config)
        primary = build_provider(
            settings.primary_provider,
            model=settings.primary_model,
            max_output_tokens=settings.max_output_tokens,
            ollama_host=settings.ollama_host,
        )
        secondary = build_provider(
            settings.secondary_provider,
            model=settings.secondary_model,
            max_output_tokens=settings.max_output_tokens,
            ollama_host=settings.ollama_host,
        )

        if args.command == "consult":
            result = ConsultOrchestrator(
                primary=primary,
                secondary=secondary,
                runs_dir=settings.runs_dir,
                save_runs=not args.no_save,
            ).consult(args.task)
        else:
            parser.error(f"Unsupported command: {args.command}")
            return 2
    except (AIReviewError, ValueError) as exc:
        print(f"ai-review: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
