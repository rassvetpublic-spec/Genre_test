import pytest

from tools.ai_review.errors import ContractError
from tools.ai_review.schema import load_schema, validate_contract


def _valid_review():
    return {
        "verdict": "PASS",
        "confidence": 0.9,
        "evidence_status": "SUFFICIENT",
        "blockers": [],
        "issues": [],
        "summary": "No blocking issue found.",
    }


def test_review_contract_accepts_valid_payload():
    validate_contract(_valid_review(), load_schema("review"))


def test_review_contract_rejects_unknown_verdict():
    payload = _valid_review()
    payload["verdict"] = "QA_APPROVED"
    with pytest.raises(ContractError):
        validate_contract(payload, load_schema("review"))


def test_review_contract_rejects_extra_properties():
    payload = _valid_review()
    payload["merge"] = True
    with pytest.raises(ContractError):
        validate_contract(payload, load_schema("review"))
