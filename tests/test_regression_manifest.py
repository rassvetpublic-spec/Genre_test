import json
from pathlib import Path

MANIFEST = Path(__file__).parent / "fixtures" / "regression_cases.json"


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


def test_xlaunge_regression_pins_the_observed_mode_split() -> None:
    case = _cases()["mode-convergence-xlaunge"]
    observed = case["observed"]

    assert case["status"] == "known_instability"
    assert observed["fast_genre"] == "Reggaeton"
    assert observed["accurate_genre"] == "Reggaeton"
    assert observed["auto_genre"] == "Drum n Bass"
    assert observed["fast_genre"] == observed["accurate_genre"]
    assert observed["auto_genre"] != observed["fast_genre"]
    assert case["expected"]["resolved_genre_stable_across_modes"] is True


def test_family_cases_are_marked_as_known_instabilities():
    cases = _cases()
    assert cases["family-consistency-za-hutorom"]["status"] == "known_instability"
    assert cases["family-consistency-live-acoustic"]["status"] == "known_instability"
