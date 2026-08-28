from pathlib import Path

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


def test_all_specialized_agents_are_repository_local() -> None:
    agent_dir = ROOT / ".github" / "agents"
    for filename, name in AGENT_NAMES.items():
        text = (agent_dir / filename).read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert f"name: {name}" in text
        assert "Read `AGENTS.md` first" in text


def test_merge_authority_is_explicit_and_single_use() -> None:
    constitution = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    workflow = (ROOT / "docs" / "AGENT_WORKFLOW.md").read_text(encoding="utf-8")
    release_manager = (
        ROOT / ".github" / "agents" / "release-manager.agent.md"
    ).read_text(encoding="utf-8")

    for text in (constitution, workflow, release_manager):
        assert "READY-MTD" in text
        assert "one merge cycle" in text.lower()
        assert "auto-merge" in text.lower()

    assert "current user instruction" in release_manager
    assert "post-merge" in release_manager.lower()


def test_path_specific_instructions_have_apply_to_frontmatter() -> None:
    instruction_dir = ROOT / ".github" / "instructions"
    for filename in (
        "audio-mastering.instructions.md",
        "github-workflow.instructions.md",
    ):
        text = (instruction_dir / filename).read_text(encoding="utf-8")
        assert text.startswith("---\napplyTo:")


def test_audio_rules_preserve_module_order_and_shared_metrics() -> None:
    text = (
        ROOT / ".github" / "instructions" / "audio-mastering.instructions.md"
    ).read_text(encoding="utf-8")
    assert "module order is semantically significant" in text
    assert "backend-neutral" in text
    assert "REAPER is the render host" in text
    assert "AUDIO_SCIENCE" in text
