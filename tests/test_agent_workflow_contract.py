import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENT_NAMES = {
    "repo-steward.agent.md": "REPO_STEWARD",
    "researcher.agent.md": "RESEARCHER",
    "architect.agent.md": "ARCHITECT",
    "coder.agent.md": "CODER",
    "qa-reviewer.agent.md": "QA_REVIEWER",
    "audio-science.agent.md": "AUDIO_SCIENCE",
    "release-manager.agent.md": "RELEASE_MANAGER",
}

ISSUE_FORM_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "agent-task.yml"
PR_TEMPLATE_PATH = ROOT / ".github" / "pull_request_template.md"
WORKFLOW_PATH = ROOT / "docs" / "AGENT_WORKFLOW.md"

INTERACTIVE_ISSUE_TYPES = {"input", "dropdown", "textarea", "checkboxes"}
ALLOWED_ISSUE_TYPES = INTERACTIVE_ISSUE_TYPES | {"markdown"}
REQUIRED_ISSUE_FORM_IDS = {
    "roadmap_phase",
    "workflow_state",
    "scope_and_paths",
    "architecture_and_dependencies",
    "acceptance_criteria",
    "reviews_and_evidence",
    "non_goals",
    "claim_metadata",
    "risks_and_decisions",
    "next_allowed_action",
}
REQUIRED_PR_HEADINGS = {
    "Workflow contract",
    "Scope",
    "Allowed paths",
    "Forbidden paths",
    "Dependencies",
    "Claim / collision check",
    "Acceptance criteria mapping",
    "Tests and CI",
    "Required reviews",
    "Produced evidence",
    "Open risks",
    "Unresolved decisions",
    "Scope audit",
    "Next allowed action",
    "MTD / release note",
}
REQUIRED_PR_WORKFLOW_FIELDS = (
    "Issue",
    "From role",
    "To role",
    "Workflow state",
    "Base SHA",
    "PR head SHA",
    "Implementation branch",
    "Roadmap phase",
)
EXACT_HEAD_MARKERS = (
    "QA_APPROVED",
    "QA_CHANGES_REQUESTED",
    "QA_BLOCKED",
    "AUDIO_APPROVED",
    "AUDIO_CHANGES_REQUESTED",
    "AUDIO_INCONCLUSIVE",
    "READY-MTD",
)
ROLE_VERDICT_MARKERS = {
    "qa-reviewer.agent.md": (
        "QA_APPROVED",
        "QA_CHANGES_REQUESTED",
        "QA_BLOCKED",
    ),
    "audio-science.agent.md": (
        "AUDIO_APPROVED",
        "AUDIO_CHANGES_REQUESTED",
        "AUDIO_INCONCLUSIVE",
    ),
    "release-manager.agent.md": ("READY-MTD",),
}
WORKFLOW_VERDICT_SECTIONS = {
    "### QA_REVIEWER": (
        "QA_APPROVED",
        "QA_CHANGES_REQUESTED",
        "QA_BLOCKED",
    ),
    "### AUDIO_SCIENCE": (
        "AUDIO_APPROVED",
        "AUDIO_CHANGES_REQUESTED",
        "AUDIO_INCONCLUSIVE",
    ),
    "### RELEASE_MANAGER": ("READY-MTD",),
    "## Exact-head readiness": ("READY-MTD",),
}
_ISSUE_NUMBER = r"[1-9][0-9]*"
_REPO_SLUG = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
CLOSING_REFERENCE = re.compile(
    rf"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+"
    rf"(?:#{_ISSUE_NUMBER}|{_REPO_SLUG}#{_ISSUE_NUMBER}|"
    rf"https?://github\.com/{_REPO_SLUG}/issues/{_ISSUE_NUMBER})\b"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_html_comments(text: str) -> str:
    assert text.count("<!--") == text.count("-->"), "unbalanced HTML comment delimiters"
    cleaned = re.sub(r"(?s)<!--.*?-->", "", text)
    assert "<!--" not in cleaned and "-->" not in cleaned, "unmatched HTML comment delimiter"
    return cleaned


def _issue_item_block(text: str, item_id: str) -> str:
    lines = text.splitlines()
    id_line = f"    id: {item_id}"
    matching_ids = [index for index, line in enumerate(lines) if line == id_line]
    assert len(matching_ids) == 1, f"expected one Issue Form id={item_id!r}"

    id_index = matching_ids[0]
    start = next(
        index
        for index in range(id_index, -1, -1)
        if lines[index].startswith("  - type: ")
    )
    end = next(
        (
            index
            for index in range(id_index + 1, len(lines))
            if lines[index].startswith("  - type: ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _pr_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    heading_line = f"## {heading}"
    matching = [index for index, line in enumerate(lines) if line == heading_line]
    assert len(matching) == 1, f"expected one PR section {heading!r}"
    start = matching[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _workflow_verdict_block(text: str, heading: str) -> str:
    heading_level = len(heading) - len(heading.lstrip("#"))
    assert heading_level in (2, 3)
    start = text.find(f"{heading}\n")
    assert start >= 0, f"missing workflow verdict section {heading!r}"
    start += len(heading) + 1
    next_heading = re.search(
        rf"(?m)^#{{2,{heading_level}}} .+$",
        text[start:],
    )
    end = start + next_heading.start() if next_heading else len(text)
    section = text[start:end]
    blocks = re.findall(r"(?ms)^```text\s*\n(.*?)^```\s*$", section)
    assert len(blocks) == 1, f"expected one text verdict block in {heading!r}"
    return blocks[0]


def test_all_specialized_agents_are_repository_local() -> None:
    agent_dir = ROOT / ".github" / "agents"
    actual_agent_files = {path.name for path in agent_dir.glob("*.agent.md")}
    assert actual_agent_files == set(AGENT_NAMES)

    for filename, name in AGENT_NAMES.items():
        text = _read(agent_dir / filename)
        assert text.startswith("---\n")
        assert f"name: {name}" in text
        assert "Read `AGENTS.md` first" in text


def test_issue_form_has_exact_required_structural_contract() -> None:
    text = _read(ISSUE_FORM_PATH)
    assert text.startswith("name: Agent implementation task\n")
    assert re.search(r"(?m)^body:$", text)

    all_types = re.findall(r"(?m)^  - type:\s*(.*?)\s*$", text)
    interactive_types = [item_type for item_type in all_types if item_type != "markdown"]
    all_ids = re.findall(r"(?m)^    id: ([a-z0-9_]+)$", text)

    assert all_types
    assert set(all_types) <= ALLOWED_ISSUE_TYPES
    assert len(interactive_types) == 10
    assert len(interactive_types) <= 10
    assert set(interactive_types) <= INTERACTIVE_ISSUE_TYPES
    assert len(all_ids) == len(set(all_ids))
    assert set(all_ids) == REQUIRED_ISSUE_FORM_IDS

    for item_id in REQUIRED_ISSUE_FORM_IDS:
        block = _issue_item_block(text, item_id)
        type_match = re.match(r"^  - type:\s*(\S+)\s*$", block.splitlines()[0])
        assert type_match is not None
        assert type_match.group(1) in INTERACTIVE_ISSUE_TYPES
        assert re.search(rf"(?m)^    id: {re.escape(item_id)}$", block)
        assert re.search(
            r"(?m)^    validations:\s*\n      required: true\s*$",
            block,
        )


def test_issue_form_creation_state_is_request_only() -> None:
    block = _issue_item_block(_read(ISSUE_FORM_PATH), "workflow_state")
    assert block.startswith("  - type: dropdown\n")

    options_match = re.search(
        r"(?ms)^      options:\s*\n(?P<options>(?:        - [^\n]+\n?)+)",
        block,
    )
    assert options_match is not None

    options = [
        line.removeprefix("        - ")
        for line in options_match.group("options").splitlines()
    ]
    assert options == ["REQUEST"]


def test_pr_template_has_required_structural_handoff_sections() -> None:
    text = _strip_html_comments(_read(PR_TEMPLATE_PATH))
    headings = re.findall(r"(?m)^## (.+)$", text)

    assert len(headings) == len(set(headings))
    assert REQUIRED_PR_HEADINGS <= set(headings)
    assert re.search(r"(?m)^Refs #\s*$", text)
    assert CLOSING_REFERENCE.search(text) is None

    workflow_contract = _pr_section(text, "Workflow contract")
    for field in REQUIRED_PR_WORKFLOW_FIELDS:
        assert re.search(rf"(?m)^- {re.escape(field)}:\s*", workflow_contract)


@pytest.mark.parametrize(
    "reference",
    (
        "Closes #131",
        "- Closes #131",
        "> Fixes #131",
        "1. Resolves #131",
        "Context: closed #131",
        "Closes owner/repo#131",
        "Fixes https://github.com/owner/repo/issues/131",
    ),
)
def test_closing_reference_detector_rejects_supported_forms(reference: str) -> None:
    assert CLOSING_REFERENCE.search(reference)


@pytest.mark.parametrize(
    "text",
    (
        "Refs #131",
        "Do not use `Closes`, `Fixes`, or `Resolves` for the implementation Issue.",
        "close the Issue after POST-MERGE-VERIFIED",
    ),
)
def test_closing_reference_detector_allows_non_closing_prose(text: str) -> None:
    assert CLOSING_REFERENCE.search(text) is None


def test_exact_head_verdict_contract_is_documented() -> None:
    workflow = _read(WORKFLOW_PATH)

    for heading, markers in WORKFLOW_VERDICT_SECTIONS.items():
        block = _workflow_verdict_block(workflow, heading)
        for marker in markers:
            declarations = [line for line in block.splitlines() if line.startswith(marker)]
            assert declarations, f"missing {marker} declaration in {heading}"
            assert set(declarations) == {f"{marker} <40-char-sha>"}


def test_authoritative_role_verdict_declarations_are_exact() -> None:
    agent_dir = ROOT / ".github" / "agents"
    for filename, markers in ROLE_VERDICT_MARKERS.items():
        text = _read(agent_dir / filename)
        for marker in markers:
            declared = re.findall(rf"(?m)^{re.escape(marker)}.*$", text)
            assert declared == [f"{marker} <40-char-sha>"]


@pytest.mark.parametrize("marker", EXACT_HEAD_MARKERS)
def test_exact_head_verdict_regex_is_strict(marker: str) -> None:
    verdict = re.compile(rf"^{re.escape(marker)} [0-9a-f]{{40}}$")
    valid_sha = "0123456789abcdef0123456789abcdef01234567"

    assert verdict.fullmatch(f"{marker} {valid_sha}")
    assert verdict.fullmatch(f"{marker} {valid_sha[:-1]}") is None
    assert verdict.fullmatch(f"{marker} {valid_sha}0") is None
    assert verdict.fullmatch(f"{marker} {valid_sha.upper()}") is None
    assert verdict.fullmatch(f"{marker}  {valid_sha}") is None
    assert verdict.fullmatch(f"{marker} {valid_sha} trailing") is None


def test_merge_authority_is_explicit_and_supports_planned_sequential_mtd() -> None:
    constitution = _read(ROOT / "AGENTS.md")
    workflow = _read(WORKFLOW_PATH)
    release_manager = _read(ROOT / ".github" / "agents" / "release-manager.agent.md")

    for text in (constitution, workflow, release_manager):
        lower = text.lower()
        assert "ready-mtd" in lower
        assert "sequential" in lower
        assert "project plan" in lower
        assert "auto-merge" in lower
        assert "scope" in lower

    assert "current conversation/project instructions" in release_manager
    assert "post-merge" in release_manager.lower()
    assert "ci fails" in release_manager.lower()


def test_path_specific_instructions_have_apply_to_frontmatter() -> None:
    instruction_dir = ROOT / ".github" / "instructions"
    for filename in (
        "audio-mastering.instructions.md",
        "github-workflow.instructions.md",
    ):
        text = _read(instruction_dir / filename)
        assert text.startswith("---\napplyTo:")


def test_audio_rules_preserve_module_order_and_shared_metrics() -> None:
    text = _read(
        ROOT / ".github" / "instructions" / "audio-mastering.instructions.md"
    )
    assert "module order is semantically significant" in text
    assert "backend-neutral" in text
    assert "REAPER is the render host" in text
    assert "AUDIO_SCIENCE" in text
