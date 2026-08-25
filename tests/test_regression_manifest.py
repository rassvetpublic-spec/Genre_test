import json
from pathlib import Path


MANIFEST = Path(__file__).parent / "fixtures" / "regression_cases_v04.json"


def _cases():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == 1
    return {item["id"]: item for item in payload["cases"]}


def test_required_real_world_regression_cases_are_registered():
    cases = _cases()
    assert {
        "tempo-short-3to2-ambiguous",
        "mode-convergence-xlaunge",
        "family-consistency-za-hutorom",
    }.issubset(cases)


def test_problem_tempo_case_does_not_claim_unverified_170_as_ground_truth():
    case = _cases()["tempo-short-3to2-ambiguous"]
    assert case["basename"] == "2_5217805607263838693.mp3"
    assert case["status"] == "ground_truth_required"
    assert case["observed"]["selected_bpm"] == 170.03
    assert case["expected"]["bpm"] is None
    assert case["expected"]["key"] == "F# minor"


def test_mode_and_family_cases_are_marked_as_known_instabilities():
    cases = _cases()
    assert cases["mode-convergence-xlaunge"]["status"] == "known_instability"
    assert cases["family-consistency-za-hutorom"]["status"] == "known_instability"
