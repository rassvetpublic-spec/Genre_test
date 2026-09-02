from __future__ import annotations

from pathlib import Path

TARGET = Path("tools/obsidian_knowledge_sync.py")
text = TARGET.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    if text.count(old) != 1:
        raise SystemExit(f"patch anchor count {text.count(old)} != 1: {old[:80]!r}")
    text = text.replace(old, new, 1)


replace_once(
    'DEFAULT_TERMS_BASE = Path("docs/obsidian/TERMS.base")\n',
    'DEFAULT_TERMS_BASE = Path("docs/obsidian/TERMS.base")\n'
    'REGISTRY_VIEW_DIR = Path("docs/obsidian/registry_views")\n'
    'REGISTRY_VIEW_PREFIX = REGISTRY_VIEW_DIR.as_posix() + "/"\n'
    'SPECIALIZED_MACHINE_STATE_PATHS = {\n'
    '    "docs/research/AI_AUDIO_TOOL_TEST_REGISTRY.json",\n'
    '}\n',
)

replace_once(
    'def registration_state(\n'
    '    path: str,\n'
    '    blob_sha: str,\n'
    '    boundary: dict[str, Any],\n'
    '    registered_paths: set[str],\n'
    ') -> str:\n'
    '    if path in GLOBAL_GENERATED_MARKDOWN:\n'
    '        return "generated_view"\n'
    '    if not _in_authoring_scope(path) or _boundary_exempt(path, boundary):\n'
    '        return "exempt"\n'
    '    baseline = boundary["baseline_blobs"]\n'
    '    if path in registered_paths:\n'
    '        return "registered"\n'
    '    if baseline.get(path) == blob_sha:\n'
    '        return "grandfathered"\n'
    '    return "registration_required"\n',
    'def registration_state(\n'
    '    path: str,\n'
    '    blob_sha: str | None,\n'
    '    boundary: dict[str, Any],\n'
    '    registered_paths: set[str],\n'
    ') -> str:\n'
    '    if path in GLOBAL_GENERATED_MARKDOWN or path.startswith(REGISTRY_VIEW_PREFIX):\n'
    '        return "generated_view"\n'
    '    if not _in_authoring_scope(path) or _boundary_exempt(path, boundary):\n'
    '        return "exempt"\n'
    '    baseline = boundary["baseline_blobs"]\n'
    '    if path in registered_paths:\n'
    '        return "registered"\n'
    '    if blob_sha is not None and baseline.get(path) == blob_sha:\n'
    '        return "grandfathered"\n'
    '    return "registration_required"\n',
)

replace_once(
    '    if path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json"):\n'
    '        return True\n'
    '    if any(path.startswith(prefix) for prefix in RADAR_GENERATED_PREFIXES):\n',
    '    if path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json"):\n'
    '        return True\n'
    '    if path in SPECIALIZED_MACHINE_STATE_PATHS:\n'
    '        return True\n'
    '    if path.startswith(REGISTRY_VIEW_PREFIX):\n'
    '        return path.endswith(".md")\n'
    '    if any(path.startswith(prefix) for prefix in RADAR_GENERATED_PREFIXES):\n',
)

replace_once(
    'def _ownership_class(path: str) -> str:\n'
    '    if path in {REGISTRY_SELF_PATH, BASELINE_PATH} or (\n'
    '        path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json")\n'
    '    ):\n'
    '        return "canonical_machine_state"\n',
    'def _ownership_class(path: str) -> str:\n'
    '    if path in {REGISTRY_SELF_PATH, BASELINE_PATH} or (\n'
    '        path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json")\n'
    '    ) or path in SPECIALIZED_MACHINE_STATE_PATHS:\n'
    '        return "canonical_machine_state"\n'
    '    if path.startswith(REGISTRY_VIEW_PREFIX):\n'
    '        return "generated_projection"\n',
)

replace_once(
    'def build_inventory(\n'
    '    tracked_blobs: dict[str, str],\n'
    '    entries: list[dict[str, Any]],\n'
    '    boundary: dict[str, Any],\n'
    ') -> tuple[dict[str, Any], list[str]]:\n'
    '    by_path = {entry["path"]: entry for entry in entries}\n'
    '    registered_paths = set(by_path)\n'
    '    paths = {\n'
    '        path for path in tracked_blobs if _is_inventory_relevant(path, registered_paths)\n'
    '    } | GLOBAL_GENERATED_OUTPUTS\n',
    'def build_inventory(\n'
    '    tracked_blobs: dict[str, str],\n'
    '    entries: list[dict[str, Any]],\n'
    '    boundary: dict[str, Any],\n'
    '    *,\n'
    '    generated_paths: set[str] | None = None,\n'
    ') -> tuple[dict[str, Any], list[str]]:\n'
    '    by_path = {entry["path"]: entry for entry in entries}\n'
    '    registered_paths = set(by_path)\n'
    '    generated = set(GLOBAL_GENERATED_OUTPUTS) | set(generated_paths or ())\n'
    '    paths = {\n'
    '        path for path in tracked_blobs if _is_inventory_relevant(path, registered_paths)\n'
    '    } | generated\n',
)

replace_once(
    '        blob_sha = None if path in GLOBAL_GENERATED_OUTPUTS else tracked_blobs.get(path)\n'
    '        state = "not_applicable"\n'
    '        if path.endswith(".md") and blob_sha is not None:\n'
    '            state = registration_state(path, blob_sha, boundary, registered_paths)\n'
    '            if state == "registration_required":\n'
    '                missing_registration.append(path)\n',
    '        blob_sha = None if path in generated else tracked_blobs.get(path)\n'
    '        state = "not_applicable"\n'
    '        if path.endswith(".md"):\n'
    '            state = registration_state(path, blob_sha, boundary, registered_paths)\n'
    '            if state == "registration_required":\n'
    '                missing_registration.append(path)\n',
)

replace_once(
    '            "research_machine_state_prefix": RADAR_MACHINE_PREFIX,\n'
    '        },\n',
    '            "research_machine_state_prefix": RADAR_MACHINE_PREFIX,\n'
    '            "specialized_machine_state_paths": sorted(SPECIALIZED_MACHINE_STATE_PATHS),\n'
    '            "registry_view_prefix": REGISTRY_VIEW_PREFIX,\n'
    '        },\n',
)

anchor = '\ndef render_knowledge_base() -> str:\n'
if text.count(anchor) != 1:
    raise SystemExit("render_knowledge_base anchor missing")
projection_code = r'''

def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def registry_view_path(canonical_path: str) -> str:
    token = hashlib.sha256(canonical_path.encode("utf-8")).hexdigest()[:20]
    return f"{REGISTRY_VIEW_PREFIX}{token}.md"


def render_registry_view(entry: dict[str, Any]) -> str:
    lines = [
        "---",
        f"title: {_yaml_scalar(entry['title'])}",
        f"doc_type: {_yaml_scalar(entry['doc_type'])}",
        f"area: {_yaml_scalar(entry['area'])}",
        f"status: {_yaml_scalar(entry['status'])}",
        f"summary: {_yaml_scalar(entry['summary'])}",
        "tags:",
    ]
    for tag in entry["tags"]:
        lines.append(f"  - {_yaml_scalar(tag)}")
    lines.extend(
        [
            "generated: true",
            f"canonical_owner: {_yaml_scalar(REGISTRY_SELF_PATH)}",
            f"canonical_path: {_yaml_scalar(entry['path'])}",
        ]
    )
    for key in sorted(OPTIONAL_LIST_KEYS | RELATION_KEYS):
        values = entry.get(key, [])
        if not values:
            continue
        lines.append(f"{key}:")
        for value in values:
            lines.append(f"  - {_yaml_scalar(value)}")
    if "reader_level" in entry:
        lines.append(f"reader_level: {_yaml_scalar(entry['reader_level'])}")
    if "language" in entry:
        lines.append(f"language: {_yaml_scalar(entry['language'])}")
    lines.extend(
        [
            "---",
            "",
            "<!-- GENERATED FROM docs/obsidian/KNOWLEDGE_REGISTRY.json; DO NOT EDIT BY HAND -->",
            "",
            f"# {entry['title']}",
            "",
            f"Canonical document: {_wiki_link(entry['path'], entry['title'])}",
            "",
        ]
    )
    return "\n".join(lines)


def render_registry_views(entries: list[dict[str, Any]]) -> dict[str, str]:
    return {
        registry_view_path(entry["path"]): render_registry_view(entry)
        for entry in sorted(entries, key=lambda item: item["path"])
    }
'''
text = text.replace(anchor, projection_code + anchor, 1)

start = text.index('def render_knowledge_base() -> str:\n')
end = text.index('\ndef build_projections(\n', start)
new_bases = r'''def render_knowledge_base() -> str:
    return """filters:\n  and:\n    - 'file.folder == \"docs/obsidian/registry_views\"'\n    - 'canonical_path != null'\nproperties:\n  canonical_path:\n    displayName: Canonical path\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  doc_type:\n    displayName: Type\n  status:\n    displayName: Status\n  summary:\n    displayName: Summary\nviews:\n  - type: table\n    name: By area\n    order:\n      - canonical_path\n      - title\n      - doc_type\n      - status\n      - summary\n    groupBy:\n      property: area\n      direction: ASC\n  - type: table\n    name: By type\n    order:\n      - canonical_path\n      - title\n      - area\n      - status\n    groupBy:\n      property: doc_type\n      direction: ASC\n  - type: table\n    name: By status\n    order:\n      - canonical_path\n      - title\n      - area\n      - doc_type\n    groupBy:\n      property: status\n      direction: ASC\n"""


def render_relations_base() -> str:
    relation_filter = "\n".join(f"        - '{key} != null'" for key in sorted(RELATION_KEYS))
    order = "\n".join(f"      - {key}" for key in sorted(RELATION_KEYS))
    return f"""filters:\n  and:\n    - 'file.folder == \"docs/obsidian/registry_views\"'\n    - or:\n{relation_filter}\nproperties:\n  canonical_path:\n    displayName: Canonical path\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  doc_type:\n    displayName: Type\nviews:\n  - type: table\n    name: Typed relations\n    order:\n      - canonical_path\n      - title\n      - area\n      - doc_type\n{order}\n    groupBy:\n      property: area\n      direction: ASC\n"""


def render_terms_base() -> str:
    return """filters:\n  and:\n    - 'file.folder == \"docs/obsidian/registry_views\"'\n    - or:\n        - 'terms != null'\n        - 'keywords_ru != null'\n        - 'keywords_en != null'\nproperties:\n  canonical_path:\n    displayName: Canonical path\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  terms:\n    displayName: Terms\n  keywords_ru:\n    displayName: Keywords RU\n  keywords_en:\n    displayName: Keywords EN\nviews:\n  - type: table\n    name: Terms and keywords\n    order:\n      - canonical_path\n      - title\n      - area\n      - terms\n      - keywords_ru\n      - keywords_en\n    groupBy:\n      property: area\n      direction: ASC\n"""
'''
text = text[:start] + new_bases + text[end:]

replace_once(
    '    blobs = tracked_blobs if tracked_blobs is not None else tracked_worktree_blobs(repo_root)\n'
    '    inventory, missing_registration = build_inventory(blobs, entries, boundary)\n',
    '    blobs = tracked_blobs if tracked_blobs is not None else tracked_worktree_blobs(repo_root)\n'
    '    registry_views = render_registry_views(entries)\n'
    '    inventory, missing_registration = build_inventory(\n'
    '        blobs, entries, boundary, generated_paths=set(registry_views)\n'
    '    )\n',
)

replace_once(
    '        DEFAULT_TERMS_BASE.as_posix(): render_terms_base(),\n'
    '    }\n',
    '        DEFAULT_TERMS_BASE.as_posix(): render_terms_base(),\n'
    '        **registry_views,\n'
    '    }\n',
)

replace_once(
    '    if stale:\n'
    '        return False, "Obsidian projection drift: " + ", ".join(stale)\n'
    '    return True, "Obsidian registry, inventory, HOME, analytics, Bases and registration gate are current"\n',
    '    view_dir = _fixed_repo_path(repo_root, REGISTRY_VIEW_DIR, field="registry view directory")\n'
    '    expected_views = {path for path in outputs if path.startswith(REGISTRY_VIEW_PREFIX)}\n'
    '    if view_dir.is_dir():\n'
    '        for candidate in sorted(view_dir.glob("*.md")):\n'
    '            relative = candidate.relative_to(repo_root).as_posix()\n'
    '            if relative not in expected_views:\n'
    '                stale.append(f"extra:{relative}")\n'
    '    if stale:\n'
    '        return False, "Obsidian projection drift: " + ", ".join(stale)\n'
    '    return True, "Obsidian registry, inventory, HOME, analytics, Bases and registration gate are current"\n',
)

replace_once(
    '    _, _, outputs, _ = build_projections(repo_root, registry_path, boundary_path)\n'
    '    for relative, content in outputs.items():\n'
    '        path = _fixed_repo_path(repo_root, Path(relative), field=f"generated output {relative}")\n'
    '        _atomic_write_text(path, content)\n',
    '    _, _, outputs, _ = build_projections(repo_root, registry_path, boundary_path)\n'
    '    view_dir = _fixed_repo_path(repo_root, REGISTRY_VIEW_DIR, field="registry view directory")\n'
    '    expected_views = {path for path in outputs if path.startswith(REGISTRY_VIEW_PREFIX)}\n'
    '    if view_dir.is_dir():\n'
    '        for candidate in sorted(view_dir.glob("*.md")):\n'
    '            relative = candidate.relative_to(repo_root).as_posix()\n'
    '            if relative not in expected_views:\n'
    '                safe = _fixed_repo_path(repo_root, Path(relative), field=f"stale registry view {relative}")\n'
    '                safe.unlink()\n'
    '    for relative, content in outputs.items():\n'
    '        path = _fixed_repo_path(repo_root, Path(relative), field=f"generated output {relative}")\n'
    '        _atomic_write_text(path, content)\n',
)

TARGET.write_text(text, encoding="utf-8", newline="\n")
