from pathlib import Path

import pytest

from tools.check_repository_context import (
    read_project_version,
    validate_repository,
    validate_texts,
)

ROOT = Path(__file__).resolve().parents[1]


def _current_texts() -> dict[str, str]:
    return {
        "active": (ROOT / "docs" / "ACTIVE_CURRENT.md").read_text(encoding="utf-8"),
        "architecture": (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        "cold_start": (ROOT / "docs" / "REPOSITORY_COLD_START.md").read_text(
            encoding="utf-8"
        ),
        "roadmap": (ROOT / "ROADMAP.md").read_text(encoding="utf-8"),
        "third_party": (ROOT / "docs" / "THIRD_PARTY_MODELS.md").read_text(
            encoding="utf-8"
        ),
        "clamp_architecture": (ROOT / "docs" / "CLAMP3_ARCHITECTURE.md").read_text(
            encoding="utf-8"
        ),
        "retrieval_acceptance": (
            ROOT / "docs" / "CLAMP3_RETRIEVAL_ACCEPTANCE.md"
        ).read_text(encoding="utf-8"),
        "clamp_runtime": (ROOT / "docs" / "CLAMP3_RUNTIME.md").read_text(
            encoding="utf-8"
        ),
        "clamp_runtime_p0": (ROOT / "docs" / "CLAMP3_RUNTIME_P0.md").read_text(
            encoding="utf-8"
        ),
        "agents": (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        "expected_version": read_project_version(ROOT),
    }


def test_current_repository_context_is_consistent() -> None:
    assert validate_repository(ROOT) == []


@pytest.mark.parametrize(
    ("component", "marker", "expected"),
    [
        (
            "active",
            "\nCurrent first implementation issue: **#27**\n",
            "Current first implementation issue: **#27**",
        ),
        (
            "active",
            "\nreleases\\Genre_test_0.4.0_portable.zip\n",
            "Genre_test_0.4.0_portable.zip",
        ),
        (
            "active",
            "\nNo v0.5 feature PR is merged to `main` until explicit MTD\n",
            "until explicit MTD",
        ),
        (
            "architecture",
            "\n# ARCHITECTURE — v0.4.0\n",
            "ARCHITECTURE — v0.4.0",
        ),
        (
            "roadmap",
            "\nisolated optional CLaMP 3 runtime until compatibility is proven\n",
            "until compatibility is proven",
        ),
        (
            "roadmap",
            "\nInitial work therefore assumes an isolated subprocess sidecar until #27 proves whether safer consolidation is possible\n",
            "until #27 proves whether safer consolidation is possible",
        ),
        (
            "third_party",
            "\nkeep them in the isolated Python 3.12 sidecar until #27 proves a safer consolidation route\n",
            "until #27 proves a safer consolidation route",
        ),
        (
            "clamp_architecture",
            "\nPreferred provisional design while #27 is open:\n",
            "Preferred provisional design while #27 is open:",
        ),
        (
            "clamp_architecture",
            "\nThe sidecar decision is provisional until compatibility measurements in #27 are complete.\n",
            "sidecar decision is provisional",
        ),
        (
            "retrieval_acceptance",
            "\nThe code block can be merged only after CI is green and explicit MTD.\n",
            "CI is green and explicit MTD",
        ),
        (
            "clamp_runtime",
            "\nStatus: **hardware validation in progress on PR #72**\n",
            "hardware validation in progress on PR #72",
        ),
        (
            "clamp_runtime",
            "\n- [ ] PR merge only after explicit MTD.\n",
            "PR merge only after explicit MTD",
        ),
        (
            "clamp_runtime_p0",
            "\nStatus: **hardware acceptance PASS on PR #72; merge still requires explicit MTD**.\n",
            "merge still requires explicit MTD",
        ),
        (
            "clamp_runtime_p0",
            "\nPR #72 and the issue implementation state must remain unmerged/open until the user gives explicit **MTD**.\n",
            "must remain unmerged/open",
        ),
    ],
)
def test_known_obsolete_markers_are_rejected(
    component: str, marker: str, expected: str
) -> None:
    texts = _current_texts()
    texts[component] += marker
    errors = validate_texts(**texts)
    assert any(expected in error for error in errors)


@pytest.mark.parametrize(
    ("component", "marker", "expected"),
    [
        ("active", "standing automatic MTD authorization", "standing automatic MTD"),
        ("architecture", "# ARCHITECTURE — current system map", "current system map"),
        ("cold_start", "NEXT ALLOWED ACTION", "NEXT ALLOWED ACTION"),
        (
            "roadmap",
            "selected isolated persistent Python 3.12 CLaMP 3 sidecar runtime (#27 complete)",
            "selected isolated persistent Python 3.12 CLaMP 3 sidecar runtime",
        ),
        (
            "third_party",
            "#27-selected isolated persistent Python 3.12 sidecar",
            "#27-selected isolated persistent Python 3.12 sidecar",
        ),
        (
            "clamp_architecture",
            "Runtime decision: **#27 complete**",
            "Runtime decision: **#27 complete**",
        ),
        (
            "retrieval_acceptance",
            "READY-MTD <exact-head-sha>",
            "READY-MTD <exact-head-sha>",
        ),
        (
            "clamp_runtime",
            "Status: **runtime decision completed and merged via PR #72 on 2026-08-27**",
            "runtime decision completed and merged via PR #72",
        ),
        (
            "clamp_runtime",
            "clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3",
            "clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3",
        ),
        (
            "clamp_runtime_p0",
            "Status: **hardware acceptance PASS; PR #72 merged on 2026-08-27 under authorized MTD**.",
            "PR #72 merged on 2026-08-27",
        ),
        (
            "clamp_runtime_p0",
            "standing automatic MTD authorization",
            "standing automatic MTD authorization",
        ),
    ],
)
def test_required_cold_start_markers_cannot_disappear(
    component: str, marker: str, expected: str
) -> None:
    texts = _current_texts()
    assert marker in texts[component]
    texts[component] = texts[component].replace(marker, "REMOVED", 1)
    errors = validate_texts(**texts)
    assert any(expected in error for error in errors)


def test_active_version_is_derived_from_project_metadata() -> None:
    texts = _current_texts()
    expected_version = texts["expected_version"]
    assert isinstance(expected_version, str)
    current_marker = f"Active development version: **{expected_version}**"
    assert current_marker in texts["active"]
    texts["active"] = texts["active"].replace(
        current_marker,
        "Active development version: **9.9.9-stale**",
        1,
    )

    errors = validate_texts(**texts)
    assert any(f"expected {expected_version}" in error for error in errors)


def test_roadmap_version_is_derived_from_project_metadata() -> None:
    texts = _current_texts()
    expected_version = texts["expected_version"]
    assert isinstance(expected_version, str)
    current_marker = (
        f"**{expected_version} — active development; "
        "no packaged stable release is currently published**"
    )
    assert current_marker in texts["roadmap"]
    texts["roadmap"] = texts["roadmap"].replace(
        current_marker,
        "**9.9.9-stale — active development; no packaged stable release is currently published**",
        1,
    )

    errors = validate_texts(**texts)
    assert any("ROADMAP: stale current development version" in error for error in errors)


def test_recovery_order_must_match_agent_constitution() -> None:
    texts = _current_texts()
    roadmap_step = "3. `ROADMAP.md` — phase context and long-term dependencies."
    issue_step = (
        "4. Assigned/open GitHub Issue plus current PR/branch state — exact task contract, "
        "acceptance criteria, allowed/forbidden paths, collision/claim status and exact-head evidence."
    )
    assert roadmap_step in texts["cold_start"]
    assert issue_step in texts["cold_start"]
    cold_start = texts["cold_start"].replace(roadmap_step, "__ROADMAP_STEP__", 1)
    cold_start = cold_start.replace(issue_step, roadmap_step, 1)
    cold_start = cold_start.replace("__ROADMAP_STEP__", issue_step, 1)
    texts["cold_start"] = cold_start

    errors = validate_texts(**texts)
    assert any("required recovery order is inconsistent with AGENTS.md" in error for error in errors)


def test_recovery_order_follows_agents_instead_of_checker_constant() -> None:
    texts = _current_texts()
    roadmap_step = "3. `ROADMAP.md` for phase context;"
    issue_step = "4. assigned GitHub Issue/task contract and current Issue/PR/branch state;"
    assert roadmap_step in texts["agents"]
    assert issue_step in texts["agents"]
    agents = texts["agents"].replace(roadmap_step, "__ROADMAP_STEP__", 1)
    agents = agents.replace(issue_step, roadmap_step, 1)
    agents = agents.replace("__ROADMAP_STEP__", issue_step, 1)
    texts["agents"] = agents

    errors = validate_texts(**texts)
    assert any("required recovery order is inconsistent with AGENTS.md" in error for error in errors)
