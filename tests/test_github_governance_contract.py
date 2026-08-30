import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULESET = ROOT / "config" / "github" / "rulesets" / "protect-main.json"
ACTIVE = ROOT / "docs" / "ACTIVE_CURRENT.md"
CHECK_CMD = ROOT / "CHECK_GOVERNANCE.cmd"


def _rule(config: dict, rule_type: str) -> dict:
    matches = [rule for rule in config["ruleset"]["rules"] if rule["type"] == rule_type]
    assert len(matches) == 1
    return matches[0]


def test_protect_main_ruleset_contract_is_hard_and_reproducible():
    config = json.loads(RULESET.read_text(encoding="utf-8"))

    assert config["repository"] == "rassvetpublic-spec/Genre_test"
    assert config["repository_assertions"]["visibility"] == "public"

    ruleset = config["ruleset"]
    assert ruleset["name"] == "Protect main"
    assert ruleset["target"] == "branch"
    assert ruleset["enforcement"] == "active"
    assert ruleset["bypass_actors"] == []
    assert ruleset["conditions"]["ref_name"] == {
        "include": ["~DEFAULT_BRANCH"],
        "exclude": [],
    }

    assert _rule(config, "deletion") == {"type": "deletion"}
    assert _rule(config, "non_fast_forward") == {"type": "non_fast_forward"}
    assert _rule(config, "required_linear_history") == {
        "type": "required_linear_history"
    }

    pull = _rule(config, "pull_request")["parameters"]
    assert pull["required_approving_review_count"] == 0
    assert pull["allowed_merge_methods"] == ["squash"]

    checks = _rule(config, "required_status_checks")["parameters"]
    assert checks["strict_required_status_checks_policy"] is True
    assert {item["context"] for item in checks["required_status_checks"]} == {
        "test (3.11)",
        "test (3.12)",
        "test (3.13)",
    }


def test_current_state_does_not_restore_retired_v04_or_explicit_mtd_only_rule():
    text = ACTIVE.read_text(encoding="utf-8")

    assert "Published stable version: **none**" in text
    assert "standing automatic MTD" in text
    assert "Stable package:" not in text
    assert "No v0.5 feature PR is merged to `main` until explicit MTD." not in text
    assert "releases\\Genre_test_0.4.0_portable.zip" not in text


def test_governance_entrypoint_checks_server_ruleset():
    text = CHECK_CMD.read_text(encoding="utf-8")
    assert "github-rulesets.ps1" in text
