from __future__ import annotations

from tools import obsidian_knowledge_sync as sync


def _entry(path: str = "docs/a.md") -> dict[str, object]:
    return {
        "path": path,
        "title": "A",
        "doc_type": "protocol",
        "area": "project",
        "status": "canonical",
        "summary": "Fixture",
        "tags": ["область/project", "тип/protocol", "статус/canonical"],
        "terms": ["fixture-term"],
        "related": ["docs/b.md"],
    }


def _boundary() -> dict[str, object]:
    return {"baseline_blobs": {}, "exempt_paths": [], "exempt_prefixes": []}


def test_registry_views_are_base_readable_projections() -> None:
    views = sync.render_registry_views([_entry()])
    assert len(views) == 1
    path, content = next(iter(views.items()))
    assert path.startswith(sync.REGISTRY_VIEW_PREFIX)
    assert 'canonical_path: "docs/a.md"' in content
    assert "terms:" in content and '  - "fixture-term"' in content
    assert "related:" in content and '  - "docs/b.md"' in content

    for rendered in (
        sync.render_knowledge_base(),
        sync.render_relations_base(),
        sync.render_terms_base(),
    ):
        assert 'file.folder == "docs/obsidian/registry_views"' in rendered
        assert "canonical_path:" in rendered


def test_specialized_machine_registry_is_in_inventory_and_fingerprint() -> None:
    entries = [_entry()]
    tracked = {
        "docs/a.md": "a" * 40,
        "docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json": "1" * 40,
    }
    inventory_a, missing_a = sync.build_inventory(tracked, entries, _boundary())
    assert missing_a == []
    records_a = {row["path"]: row for row in inventory_a["entries"]}
    specialized = records_a["docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json"]
    assert specialized["ownership_class"] == "canonical_machine_state"

    tracked["docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json"] = "2" * 40
    inventory_b, missing_b = sync.build_inventory(tracked, entries, _boundary())
    assert missing_b == []
    assert inventory_a["source_fingerprint"] != inventory_b["source_fingerprint"]


def test_generated_markdown_is_classified_without_blob_identity() -> None:
    entries = [_entry()]
    views = sync.render_registry_views(entries)
    inventory, missing = sync.build_inventory(
        {"docs/a.md": "a" * 40},
        entries,
        _boundary(),
        generated_paths=set(views),
    )
    assert missing == []
    records = {row["path"]: row for row in inventory["entries"]}
    assert records[sync.DEFAULT_HOME.as_posix()]["registration_state"] == "generated_view"
    view_path = next(iter(views))
    assert records[view_path]["registration_state"] == "generated_view"
    assert records[view_path]["ownership_class"] == "generated_projection"
