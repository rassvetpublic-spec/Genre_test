from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .context import build_context, canonical_json, context_sha256
from .providers.base import StructuredProvider
from .schema import load_schema, validate_contract


_PROMPT_DIR = Path(__file__).resolve().with_name("prompts")


def _prompt(name: str) -> str:
    return (_PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def _context_input(context_json: str, tail: str) -> str:
    return f"<context_pack>\n{context_json}\n</context_pack>\n\n{tail.strip()}"


class ConsultOrchestrator:
    def __init__(
        self,
        *,
        openai: StructuredProvider,
        gemini: StructuredProvider,
        runs_dir: str | Path,
        save_runs: bool = True,
    ) -> None:
        self.openai = openai
        self.gemini = gemini
        self.runs_dir = Path(runs_dir)
        self.save_runs = save_runs

    def consult(self, task: str) -> dict[str, Any]:
        context = build_context(task)
        context_json = canonical_json(context)
        digest = context_sha256(context_json)

        proposal_schema = load_schema("proposal")
        review_schema = load_schema("review")

        openai_proposal = self.openai.generate_json(
            instructions=_prompt("solver"),
            input_text=_context_input(
                context_json,
                "Produce Proposal A independently. Do not assume access to the other provider.",
            ),
            schema=proposal_schema,
            schema_name="proposal",
        )
        validate_contract(openai_proposal, proposal_schema)

        gemini_proposal = self.gemini.generate_json(
            instructions=_prompt("solver"),
            input_text=_context_input(
                context_json,
                "Produce Proposal B independently. Do not assume access to the other provider.",
            ),
            schema=proposal_schema,
            schema_name="proposal",
        )
        validate_contract(gemini_proposal, proposal_schema)

        openai_review = self.openai.generate_json(
            instructions=_prompt("reviewer"),
            input_text=_context_input(
                context_json,
                "<proposal provider=\"gemini\">\n"
                f"{canonical_json(gemini_proposal)}\n"
                "</proposal>\nReview this proposal against the supplied ContextPack.",
            ),
            schema=review_schema,
            schema_name="review",
        )
        validate_contract(openai_review, review_schema)

        gemini_review = self.gemini.generate_json(
            instructions=_prompt("reviewer"),
            input_text=_context_input(
                context_json,
                "<proposal provider=\"openai\">\n"
                f"{canonical_json(openai_proposal)}\n"
                "</proposal>\nReview this proposal against the supplied ContextPack.",
            ),
            schema=review_schema,
            schema_name="review",
        )
        validate_contract(gemini_review, review_schema)

        synthesis_payload = (
            "<proposal provider=\"openai\">\n"
            f"{canonical_json(openai_proposal)}\n</proposal>\n"
            "<proposal provider=\"gemini\">\n"
            f"{canonical_json(gemini_proposal)}\n</proposal>\n"
            "<review provider=\"openai\" target=\"gemini\">\n"
            f"{canonical_json(openai_review)}\n</review>\n"
            "<review provider=\"gemini\" target=\"openai\">\n"
            f"{canonical_json(gemini_review)}\n</review>\n"
            "Synthesize the strongest final proposal. Preserve unresolved risks and evidence gaps."
        )
        final_proposal = self.openai.generate_json(
            instructions=_prompt("synthesizer"),
            input_text=_context_input(context_json, synthesis_payload),
            schema=proposal_schema,
            schema_name="final_proposal",
        )
        validate_contract(final_proposal, proposal_schema)

        result = {
            "run": {
                "state": "COMPLETE",
                "round": 1,
                "max_rounds": 1,
                "openai_completed": True,
                "gemini_completed": True,
                "context_sha256": digest,
            },
            "context": context,
            "proposals": {
                "openai": openai_proposal,
                "gemini": gemini_proposal,
            },
            "reviews": {
                "openai_on_gemini": openai_review,
                "gemini_on_openai": gemini_review,
            },
            "final": final_proposal,
        }

        if self.save_runs:
            result["run"]["artifact"] = str(self._save_result(result))
        return result

    def _save_result(self, result: dict[str, Any]) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        run_id = result["context"]["run_id"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.runs_dir / f"{stamp}_{run_id}.json"
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path
