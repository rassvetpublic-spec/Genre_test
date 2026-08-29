import hashlib
import importlib
from pathlib import Path
import sys


_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_cli = importlib.import_module("tools.ai_review.cli")
_orchestrator = importlib.import_module("tools.ai_review.orchestrator")
build_parser = _cli.build_parser
ConsultOrchestrator = _orchestrator.ConsultOrchestrator


class FakeProvider:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def generate_json(self, *, instructions, input_text, schema, schema_name):
        self.calls.append(
            {
                "instructions": instructions,
                "input_text": input_text,
                "schema": schema,
                "schema_name": schema_name,
            }
        )
        if schema_name == "review":
            return {
                "verdict": "PASS",
                "confidence": 0.9,
                "evidence_status": "SUFFICIENT",
                "blockers": [],
                "issues": [],
                "summary": f"{self.name} review",
            }
        return {
            "title": f"{self.name} {schema_name}",
            "summary": "summary",
            "recommendation": "recommendation",
            "assumptions": [],
            "risks": [],
            "steps": ["step"],
            "evidence_needed": [],
        }


def _extract_context(text):
    start_marker = "<context_pack>\n"
    end_marker = "\n</context_pack>"
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_consult_uses_same_canonical_context_for_every_stage(tmp_path):
    openai = FakeProvider("openai")
    gemini = FakeProvider("gemini")
    result = ConsultOrchestrator(
        openai=openai,
        gemini=gemini,
        runs_dir=tmp_path,
        save_runs=False,
    ).consult("Choose a bounded implementation.")

    calls = openai.calls + gemini.calls
    contexts = [_extract_context(call["input_text"]) for call in calls]
    assert len(set(contexts)) == 1

    digest = hashlib.sha256(contexts[0].encode("utf-8")).hexdigest()
    assert result["run"]["context_sha256"] == digest
    assert result["run"]["state"] == "COMPLETE"
    assert result["final"]["recommendation"] == "recommendation"


def test_cli_exposes_consult_without_importing_provider_sdks():
    parser = build_parser()
    args = parser.parse_args(["consult", "--task", "x", "--no-save"])
    assert args.command == "consult"
    assert args.task == "x"
