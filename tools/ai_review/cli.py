from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import load_settings
from .errors import AIReviewError
from .orchestrator import ConsultOrchestrator
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ai_review",
        description="Local OpenAI ↔ Gemini cross-model consultation.",
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
        openai = OpenAIProvider(
            model=settings.openai_model,
            max_output_tokens=settings.max_output_tokens,
        )
        gemini = GeminiProvider(model=settings.gemini_model)

        if args.command == "consult":
            result = ConsultOrchestrator(
                openai=openai,
                gemini=gemini,
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
