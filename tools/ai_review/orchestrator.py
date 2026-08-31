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


def _provider_metadata(provider: StructuredProvider) -> dict[str, str]:
    model = getattr(provider, "model", "unknown")
    return {"name": provider.name, "model": str(model)}


class ConsultOrchestrator:
    def __init__(
        self,
        *,
        primary: StructuredProvider,
        secondary: StructuredProvider,
        runs_dir: str | Path,
        save_runs: bool = True,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.runs_dir = Path(runs_dir)
        self.save_runs = save_runs

    def consult(self, task: str) -> dict[str, Any]:
        context = build_context(task)
        context_json = canonical_json(context)
        digest = context_sha256(context_json)

        proposal_schema = load_schema("proposal")
        review_schema = load_schema("review")

        primary_proposal = self.primary.generate_json(
            instructions=_prompt("solver"),
            input_text=_context_input(
                context_json,
                "Produce Proposal A independently. Do not assume access to the other provider.",
            ),
            schema=proposal_schema,
            schema_name="proposal",
        )
        validate_contract(primary_proposal, proposal_schema)

        secondary_proposal = self.secondary.generate_json(
            instructions=_prompt("solver"),
            input_text=_context_input(
                context_json,
                "Produce Proposal B independently. Do not assume access to the other provider.",
            ),
            schema=proposal_schema,
            schema_name="proposal",
        )
        validate_contract(secondary_proposal, proposal_schema)

        primary_review = self.primary.generate_json(
            instructions=_prompt("reviewer"),
            input_text=_context_input(
                context_json,
                f"<proposal role=\"secondary\" provider=\"{self.secondary.name}\">\n"
                f"{canonical_json(secondary_proposal)}\n"
                "</proposal>\nReview this proposal against the supplied ContextPack.",
            ),
            schema=review_schema,
            schema_name="review",
        )
        validate_contract(primary_review, review_schema)

        secondary_review = self.secondary.generate_json(
            instructions=_prompt("reviewer"),
            input_text=_context_input(
                context_json,
                f"<proposal role=\"primary\" provider=\"{self.primary.name}\">\n"
                f"{canonical_json(primary_proposal)}\n"
                "</proposal>\nReview this proposal against the supplied ContextPack.",
            ),
            schema=review_schema,
            schema_name="review",
        )
        validate_contract(secondary_review, review_schema)

        synthesis_payload = (
            f"<proposal role=\"primary\" provider=\"{self.primary.name}\">\n"
            f"{canonical_json(primary_proposal)}\n</proposal>\n"
            f"<proposal role=\"secondary\" provider=\"{self.secondary.name}\">\n"
            f"{canonical_json(secondary_proposal)}\n</proposal>\n"
            f"<review provider=\"{self.primary.name}\" target=\"secondary\">\n"
            f"{canonical_json(primary_review)}\n</review>\n"
            f"<review provider=\"{self.secondary.name}\" target=\"primary\">\n"
            f"{canonical_json(secondary_review)}\n</review>\n"
            "Synthesize the strongest final proposal. Preserve unresolved risks and evidence gaps."
        )
        final_proposal = self.primary.generate_json(
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
                "primary_completed": True,
                "secondary_completed": True,
                "context_sha256": digest,
            },
            "providers": {
                "primary": _provider_metadata(self.primary),
                "secondary": _provider_metadata(self.secondary),
            },
            "context": context,
            "proposals": {
                "primary": primary_proposal,
                "secondary": secondary_proposal,
            },
            "reviews": {
                "primary_on_secondary": primary_review,
                "secondary_on_primary": secondary_review,
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
