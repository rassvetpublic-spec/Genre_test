from __future__ import annotations

import importlib.util
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
