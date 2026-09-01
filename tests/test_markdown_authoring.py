from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.check_markdown_authoring import (
    AuthoringError,
    _git_blob_sha,
    load_baseline,
    validate_repository,
    verify_baseline_against_git,
)


def _baseline(path: str, data: bytes) -> dict[str, object]:
    return {
        "schema": "genre-test-markdown-legacy-baseline-v1",
        "schema_version": 1,
        "baseline_commit": "0" * 40,
        "scope": ["docs/**/*.md"],
        "exempt_prefixes": ["docs/research/obsidian/"],
        "exempt_paths": ["docs/obsidian/KNOWLEDGE_INDEX.md"],
        "baseline_blobs": {path: _git_blob_sha(data)},
    }


def _compliant(title: str = "Example") -> bytes:
    return (
        "---\n"
        f'title: "{title}"\n'
        "doc_type: guide\n"
        "area: project\n"
        "status: active\n"
        'summary: "Example summary."\n'
        "tags:\n"
        "  - область/project\n"
        "  - тип/guide\n"
        "  - статус/active\n"
        "---\n\n"
        f"# {title}\n\n"
        "## Section\n\n"
        "Text.\n"
    ).encode()


def test_unchanged_grandfathered_markdown_passes(tmp_path: Path) -> None:
    path = "docs/old.md"
    data = b"# Historical file without passport\n"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes(data)

    errors = validate_repository(tmp_path, _baseline(path, data), tracked_paths=[path])
    assert errors == []


def test_new_noncompliant_markdown_fails(tmp_path: Path) -> None:
    path = "docs/new.md"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text("# Missing passport\n", encoding="utf-8", newline="\n")

    errors = validate_repository(tmp_path, _baseline("docs/old.md", b"old"), tracked_paths=[path])
    assert any("missing opening frontmatter delimiter" in error for error in errors)


def test_changed_grandfathered_markdown_requires_passport(tmp_path: Path) -> None:
    path = "docs/old.md"
    old = b"# Historical\n"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text("# Changed without passport\n", encoding="utf-8", newline="\n")

    errors = validate_repository(tmp_path, _baseline(path, old), tracked_paths=[path])
    assert any("missing opening frontmatter delimiter" in error for error in errors)


def test_new_and_migrated_compliant_markdown_pass(tmp_path: Path) -> None:
    old_path = "docs/old.md"
    new_path = "docs/new.md"
    target_old = tmp_path / old_path
    target_new = tmp_path / new_path
    target_old.parent.mkdir(parents=True)
    target_old.write_bytes(_compliant("Migrated"))
    target_new.write_bytes(_compliant("New"))

    errors = validate_repository(
        tmp_path,
        _baseline(old_path, b"# Historical\n"),
        tracked_paths=[old_path, new_path],
    )
    assert errors == []


def test_generated_projection_prefix_is_exempt(tmp_path: Path) -> None:
    path = "docs/research/obsidian/generated.md"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text("generated without human passport\n", encoding="utf-8", newline="\n")

    errors = validate_repository(tmp_path, _baseline("docs/old.md", b"old"), tracked_paths=[path])
    assert errors == []


def test_heading_level_skip_fails(tmp_path: Path) -> None:
    path = "docs/new.md"
    bad = _compliant("Bad").replace(b"## Section", b"### Skipped")
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes(bad)

    errors = validate_repository(tmp_path, _baseline("docs/old.md", b"old"), tracked_paths=[path])
    assert any("heading level skip" in error for error in errors)


def test_current_baseline_is_anchored_to_pinned_git_tree() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    baseline = load_baseline(repo_root / "docs/obsidian/MARKDOWN_LEGACY_BASELINE.json")
    verify_baseline_against_git(repo_root, baseline)


def test_changed_baseline_blob_identity_is_rejected() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    baseline = load_baseline(repo_root / "docs/obsidian/MARKDOWN_LEGACY_BASELINE.json")
    blobs = dict(baseline["baseline_blobs"])
    first_path = min(blobs)
    blobs[first_path] = "0" * 40
    baseline["baseline_blobs"] = blobs

    with pytest.raises(AuthoringError, match="blob identities"):
        verify_baseline_against_git(repo_root, baseline)


def test_exemption_set_cannot_be_widened_in_manifest(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "docs/obsidian/MARKDOWN_LEGACY_BASELINE.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["exempt_prefixes"].append("docs/")
    tampered = tmp_path / "baseline.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AuthoringError, match="exempt_prefixes"):
        load_baseline(tampered)


def test_current_repository_markdown_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    baseline = load_baseline(repo_root / "docs/obsidian/MARKDOWN_LEGACY_BASELINE.json")
    verify_baseline_against_git(repo_root, baseline)
    errors = validate_repository(repo_root, baseline)
    assert errors == []
