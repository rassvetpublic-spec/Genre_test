from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "research_radar_sync", ROOT / "tools" / "research_radar_sync.py"
)
assert SPEC is not None and SPEC.loader is not None
radar = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(radar)


def test_research_radar_projection_is_in_sync() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/research_radar_sync.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_research_radar_state_is_structurally_valid() -> None:
    topics, sources, state = radar.load_state(ROOT)
    radar.validate_state(topics, sources, state, ROOT)


def test_manual_notes_are_preserved() -> None:
    existing = (
        "---\nid: sample\n---\n"
        f"{radar.MANUAL_START}\nkeep this note\n[[Custom Link]]\n{radar.MANUAL_END}\n"
    )
    notes = radar.extract_manual_notes(existing)
    assert "keep this note" in notes
    assert "[[Custom Link]]" in notes


def test_manual_notes_with_placeholder_and_real_text_are_not_empty() -> None:
    notes = f"\n{radar.MANUAL_PLACEHOLDER}\nreal note\n"
    assert radar._real_manual_notes(notes)


def test_legacy_prompt_is_compatibility_only() -> None:
    text = (
        ROOT / "docs" / "development" / "research_radar" / "RESEARCH_PROMPT.md"
    ).read_text(encoding="utf-8")
    assert "compatibility" in text.lower()
    assert "docs/research/RESEARCH_OPERATING_RULES.md" in text
    assert "docs/research/RESEARCH_RADAR.md" in text
    assert "independent copy" in text


def test_legacy_runs_path_redirects_to_canonical_runs() -> None:
    text = (
        ROOT
        / "docs"
        / "development"
        / "research_radar"
        / "runs"
        / "README.md"
    ).read_text(encoding="utf-8")
    assert "../../../research/runs/" in text
    assert "raw search dumps" in text


def test_keyword_map_is_generated_view_of_radar_topics() -> None:
    text = (
        ROOT / "docs" / "development" / "research_radar" / "KEYWORD_MAP.md"
    ).read_text(encoding="utf-8")
    assert radar.MARKER in text
    assert "RADAR_TOPICS.json" in text
    assert "Canonical research keyword/topic semantics" in text


def test_projection_uses_globally_unique_note_names() -> None:
    obs = ROOT / "docs" / "research" / "obsidian"
    assert (obs / "RESEARCH_HOME.md").is_file()
    assert (obs / "RESEARCH_STATE.md").is_file()
    assert not (obs / "HOME.md").exists()
    assert not (obs / "STATE.md").exists()
    topic_names = [p.name for p in (obs / "TOPICS").glob("*.md")]
    source_names = [p.name for p in (obs / "SOURCES").glob("*.md")]
    assert topic_names and all(name.startswith("topic__") for name in topic_names)
    assert source_names and all(name.startswith("source__") for name in source_names)


def test_research_home_declares_one_vault_and_projection_boundary() -> None:
    text = (
        ROOT / "docs" / "research" / "obsidian" / "RESEARCH_HOME.md"
    ).read_text(encoding="utf-8")
    assert "Vault root: repository root `Genre_test/`." in text
    assert "generated Research-domain projection" in text
    assert "docs/obsidian/" in text
    assert "must not duplicate mutable Radar state" in text


def test_stale_generated_nodes_are_detected(tmp_path: Path) -> None:
    stale = tmp_path / "docs" / "research" / "obsidian" / "TOPICS" / "old.md"
    stale.parent.mkdir(parents=True)
    stale.write_text(f"{radar.MARKER}\n", encoding="utf-8")
    assert radar._stale_generated_files(set(), tmp_path) == [stale]


def test_manual_notes_reject_duplicate_marker_pairs() -> None:
    text = (
        f"{radar.MANUAL_START}\none\n{radar.MANUAL_END}\n"
        f"{radar.MANUAL_START}\ntwo\n{radar.MANUAL_END}\n"
    )
    try:
        radar.extract_manual_notes(text)
    except radar.RadarError:
        pass
    else:
        raise AssertionError("duplicate manual-note pairs must fail closed")


def test_canonical_path_cannot_escape_repository(tmp_path: Path) -> None:
    (tmp_path / "docs" / "research" / "data").mkdir(parents=True)
    outside = tmp_path.parent / "outside-radar-test.md"
    outside.write_text("outside", encoding="utf-8")
    topics = {
        "schema_version": 1,
        "authority": "canonical_machine_state",
        "topics": [
            {
                "id": "topic",
                "status": "ACTIVE",
                "keywords": ["x"],
                "exclusions": ["y"],
            }
        ],
    }
    sources = {
        "schema_version": 1,
        "authority": "canonical_machine_state",
        "entries": [
            {
                "id": "source",
                "topics": ["topic"],
                "canonical_path": "../outside-radar-test.md",
            }
        ],
    }
    state = {
        "schema_version": 1,
        "authority": "canonical_machine_state",
        "run_sequence": 0,
        "known_source_ids": ["source"],
        "topic_state": {"topic": {"status": "NOT_RUN"}},
        "suppressed_candidates": [],
        "follow_up": [],
    }
    try:
        radar.validate_state(topics, sources, state, tmp_path)
    except radar.RadarError:
        pass
    else:
        raise AssertionError("canonical_path traversal must fail closed")
    finally:
        outside.unlink(missing_ok=True)


def _seed_minimal_radar(tmp_path: Path) -> None:
    data = tmp_path / "docs" / "research" / "data"
    data.mkdir(parents=True)
    target = tmp_path / "docs" / "source.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# source\n", encoding="utf-8")
    (data / "RADAR_TOPICS.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "authority": "canonical_machine_state",
                "topics": [
                    {
                        "id": "topic",
                        "title": "Topic",
                        "status": "ACTIVE",
                        "keywords": ["x"],
                        "exclusions": ["y"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (data / "SOURCE_REGISTRY.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "authority": "canonical_machine_state",
                "entries": [
                    {
                        "id": "source",
                        "title": "Source",
                        "kind": "reference",
                        "status": "ACTIVE",
                        "canonical_path": "docs/source.md",
                        "topics": ["topic"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (data / "RESEARCH_STATE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "authority": "canonical_machine_state",
                "run_sequence": 0,
                "last_run": None,
                "last_successful_run": None,
                "known_source_ids": ["source"],
                "topic_state": {
                    "topic": {"status": "NOT_RUN", "last_checked": None}
                },
                "suppressed_candidates": [],
                "follow_up": [],
            }
        ),
        encoding="utf-8",
    )


def test_rename_migration_preserves_manual_notes(tmp_path: Path) -> None:
    _seed_minimal_radar(tmp_path)
    old = tmp_path / "docs" / "research" / "obsidian" / "HOME.md"
    old.parent.mkdir(parents=True)
    old.write_text(
        f"{radar.MARKER}\n"
        f"{radar.MANUAL_START}\ncustom note\n{radar.MANUAL_END}\n",
        encoding="utf-8",
    )
    assert radar.sync(tmp_path, check=False) == 0
    new = tmp_path / "docs" / "research" / "obsidian" / "RESEARCH_HOME.md"
    assert "custom note" in new.read_text(encoding="utf-8")
    assert not old.exists()


def test_protected_stale_page_fails_before_any_projection_write(tmp_path: Path) -> None:
    _seed_minimal_radar(tmp_path)
    stale = (
        tmp_path
        / "docs"
        / "research"
        / "obsidian"
        / "TOPICS"
        / "unregistered.md"
    )
    stale.parent.mkdir(parents=True)
    stale.write_text(
        f"{radar.MARKER}\n"
        f"{radar.MANUAL_START}\n"
        f"{radar.MANUAL_PLACEHOLDER}\nreal note\n"
        f"{radar.MANUAL_END}\n",
        encoding="utf-8",
    )
    try:
        radar.sync(tmp_path, check=False)
    except radar.RadarError:
        pass
    else:
        raise AssertionError("protected stale page must block regeneration")
    assert not (
        tmp_path / "docs" / "research" / "obsidian" / "RESEARCH_HOME.md"
    ).exists()
