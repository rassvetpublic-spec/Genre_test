from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "genre-test-obsidian-knowledge-registry-v1"
AUTHORITY_SCOPE = "knowledge_navigation_metadata_only"
GENERATION_DIRECTION = "JSON_TO_MARKDOWN"

DOC_TYPES = {
    "architecture",
    "protocol",
    "reference",
    "research",
    "decision",
    "runbook",
    "status",
    "index",
    "guide",
    "machine_prompt",
}
AREAS = {
    "project",
    "retrieval",
    "audio-analysis",
    "mastering",
    "repair",
    "runtime",
    "research",
    "agents",
    "delivery",
}
STATUSES = {"canonical", "active", "proposal", "reference", "archived", "generated"}
RELATION_KEYS = {
    "parent",
    "depends_on",
    "implementation_of",
    "supersedes",
    "superseded_by",
    "evidence_for",
    "research_for",
    "related",
}
OPTIONAL_LIST_KEYS = {"aliases", "terms", "keywords_ru", "keywords_en"}
READER_LEVELS = {"basic", "intermediate", "expert", "machine"}
REQUIRED_ENTRY_KEYS = {"path", "title", "doc_type", "area", "status", "summary", "tags"}
ALLOWED_ENTRY_KEYS = (
    REQUIRED_ENTRY_KEYS
    | OPTIONAL_LIST_KEYS
    | RELATION_KEYS
    | {"reader_level", "source_of_truth", "language"}
)

DEFAULT_REGISTRY = Path("docs/obsidian/KNOWLEDGE_REGISTRY.json")
DEFAULT_OUTPUT = Path("docs/obsidian/KNOWLEDGE_INDEX.md")

REGISTRY_SELF_PATH = DEFAULT_REGISTRY.as_posix()
GENERATED_INDEX_PATH = DEFAULT_OUTPUT.as_posix()
FORBIDDEN_RADAR_PREFIXES = (
    "docs/research/data/",
    "docs/research/obsidian/",
    "docs/development/research_radar/",
)


class RegistryError(ValueError):
    """Raised when the knowledge registry violates the Phase 1 contract."""


def _safe_repo_path(raw: Any, *, field: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw.strip():
        raise RegistryError(f"{field}: expected a non-empty repository-relative path")
    if "\\" in raw:
        raise RegistryError(f"{field}: use forward slashes in repository paths: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("/") or ".." in path.parts:
        raise RegistryError(f"{field}: path traversal/absolute path is forbidden: {raw!r}")
    if any(part in {"", "."} for part in path.parts):
        raise RegistryError(f"{field}: non-normalized path is forbidden: {raw!r}")
    return path


def _require_string(entry: dict[str, Any], key: str, label: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{label}.{key}: expected a non-empty string")
    return value.strip()


def _validate_string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RegistryError(f"{field}: expected a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise RegistryError(f"{field}: all values must be non-empty strings")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise RegistryError(f"{field}: duplicate values are forbidden")
    return normalized


def _is_forbidden_radar_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in FORBIDDEN_RADAR_PREFIXES)


def load_registry(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"registry not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryError(f"invalid registry JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError("registry root must be a JSON object")
    return data


def validate_registry(data: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    if data.get("schema") != SCHEMA:
        raise RegistryError(f"schema must be {SCHEMA!r}")
    if data.get("schema_version") != 1:
        raise RegistryError("schema_version must be 1")
    if data.get("authority_scope") != AUTHORITY_SCOPE:
        raise RegistryError(f"authority_scope must be {AUTHORITY_SCOPE!r}")
    if data.get("generation_direction") != GENERATION_DIRECTION:
        raise RegistryError(f"generation_direction must be {GENERATION_DIRECTION!r}")

    allowed_root_keys = {"schema", "schema_version", "authority_scope", "generation_direction", "entries"}
    unknown_root = sorted(set(data) - allowed_root_keys)
    if unknown_root:
        raise RegistryError(f"registry root has unsupported keys: {', '.join(unknown_root)}")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RegistryError("entries must be a non-empty list")

    seen_paths: set[str] = set()
    normalized_entries: list[dict[str, Any]] = []

    for index, raw_entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(raw_entry, dict):
            raise RegistryError(f"{label}: entry must be an object")

        unknown_keys = sorted(set(raw_entry) - ALLOWED_ENTRY_KEYS)
        if unknown_keys:
            raise RegistryError(f"{label}: unsupported keys: {', '.join(unknown_keys)}")

        missing = sorted(REQUIRED_ENTRY_KEYS - raw_entry.keys())
        if missing:
            raise RegistryError(f"{label}: missing required keys: {', '.join(missing)}")

        raw_path = _require_string(raw_entry, "path", label)
        rel_path = _safe_repo_path(raw_path, field=f"{label}.path")
        path_text = rel_path.as_posix()

        if path_text in {REGISTRY_SELF_PATH, GENERATED_INDEX_PATH}:
            raise RegistryError(f"{label}.path: registry/generated index cannot register itself: {path_text}")
        if _is_forbidden_radar_path(path_text):
            raise RegistryError(
                f"{label}.path: Research Radar-owned mutable/generated path is forbidden in the global registry: {path_text}"
            )
        if path_text in seen_paths:
            raise RegistryError(f"{label}.path: duplicate registry path: {path_text}")
        seen_paths.add(path_text)

        absolute = repo_root.joinpath(*rel_path.parts)
        if not absolute.is_file():
            raise RegistryError(f"{label}.path: referenced file does not exist: {path_text}")

        title = _require_string(raw_entry, "title", label)
        doc_type = _require_string(raw_entry, "doc_type", label)
        area = _require_string(raw_entry, "area", label)
        status = _require_string(raw_entry, "status", label)
        summary = _require_string(raw_entry, "summary", label)

        if doc_type not in DOC_TYPES:
            raise RegistryError(f"{label}.doc_type: unsupported value {doc_type!r}")
        if area not in AREAS:
            raise RegistryError(f"{label}.area: unsupported Genre_test area {area!r}")
        if status not in STATUSES:
            raise RegistryError(f"{label}.status: unsupported value {status!r}")

        tags = _validate_string_list(raw_entry.get("tags"), field=f"{label}.tags")
        expected_tags = {
            f"область/{area}",
            f"тип/{doc_type.replace('_', '-')}",
            f"статус/{status}",
        }
        if set(tags) != expected_tags:
            missing_tags = sorted(expected_tags - set(tags))
            extra_tags = sorted(set(tags) - expected_tags)
            details: list[str] = []
            if missing_tags:
                details.append(f"missing: {', '.join(missing_tags)}")
            if extra_tags:
                details.append(f"unapproved: {', '.join(extra_tags)}")
            raise RegistryError(f"{label}.tags: controlled taxonomy mismatch ({'; '.join(details)})")
        for tag in tags:
            if " " in tag:
                raise RegistryError(f"{label}.tags: spaces are forbidden in controlled tag {tag!r}")

        normalized: dict[str, Any] = {
            "path": path_text,
            "title": title,
            "doc_type": doc_type,
            "area": area,
            "status": status,
            "summary": summary,
            "tags": tags,
        }

        for key in OPTIONAL_LIST_KEYS:
            if key in raw_entry:
                normalized[key] = _validate_string_list(raw_entry[key], field=f"{label}.{key}")

        if "reader_level" in raw_entry:
            reader_level = _require_string(raw_entry, "reader_level", label)
            if reader_level not in READER_LEVELS:
                raise RegistryError(f"{label}.reader_level: unsupported value {reader_level!r}")
            normalized["reader_level"] = reader_level

        if "source_of_truth" in raw_entry:
            source_of_truth = raw_entry["source_of_truth"]
            if not isinstance(source_of_truth, bool):
                raise RegistryError(f"{label}.source_of_truth: expected boolean")
            if source_of_truth and status != "canonical":
                raise RegistryError(f"{label}.source_of_truth: true requires status='canonical'")
            normalized["source_of_truth"] = source_of_truth

        if "language" in raw_entry:
            normalized["language"] = _require_string(raw_entry, "language", label)

        for relation in RELATION_KEYS:
            if relation not in raw_entry:
                continue
            targets = _validate_string_list(raw_entry[relation], field=f"{label}.{relation}")
            normalized_targets: list[str] = []
            for target_index, target in enumerate(targets):
                target_path = _safe_repo_path(target, field=f"{label}.{relation}[{target_index}]")
                target_text = target_path.as_posix()
                target_file = repo_root.joinpath(*target_path.parts)
                if not target_file.is_file():
                    raise RegistryError(
                        f"{label}.{relation}[{target_index}]: relation target does not exist: {target_text}"
                    )
                if target_text == path_text:
                    raise RegistryError(f"{label}.{relation}: self-reference is forbidden: {path_text}")
                normalized_targets.append(target_text)
            normalized[relation] = normalized_targets

        normalized_entries.append(normalized)

    return normalized_entries


def _wiki_target(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _wiki_link(path: str, title: str) -> str:
    safe_title = title.replace("|", "-")
    return f"[[{_wiki_target(path)}|{safe_title}]]"


def render_index(data: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    by_path = {entry["path"]: entry for entry in entries}
    by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_area[entry["area"]].append(entry)

    lines = [
        "---",
        'id: "genre-test-knowledge-index"',
        'type: "knowledge_index"',
        "generated: true",
        f'canonical_owner: "{REGISTRY_SELF_PATH}"',
        f'generation_direction: "{data["generation_direction"]}"',
        "---",
        "",
        "<!-- GENERATED BY tools/obsidian_knowledge_sync.py; DO NOT EDIT BY HAND -->",
        "",
        "# Genre_test Knowledge Index",
        "",
        "> Derived/rebuildable navigation view. Canonical project facts remain in their owning repository documents/state; this index never overrides them.",
        "",
        f"Registered principal documents: **{len(entries)}**.",
        "",
        "Coverage is intentionally partial in Phase 1. Unregistered files are not implied to be unimportant, deprecated, or non-canonical.",
        "",
        "## Areas",
        "",
    ]

    for area in sorted(by_area):
        lines.append(f"### `{area}`")
        lines.append("")
        lines.append("| Document | Type | Status | Summary |")
        lines.append("|---|---|---|---|")
        for entry in sorted(by_area[area], key=lambda item: (item["title"].casefold(), item["path"])):
            link = _wiki_link(entry["path"], entry["title"])
            summary = entry["summary"].replace("|", "\\|")
            lines.append(f"| {link} | `{entry['doc_type']}` | `{entry['status']}` | {summary} |")
        lines.append("")

    relation_rows: list[tuple[str, str, str]] = []
    for entry in sorted(entries, key=lambda item: item["path"]):
        source_link = _wiki_link(entry["path"], entry["title"])
        for relation in sorted(RELATION_KEYS):
            for target in entry.get(relation, []):
                target_entry = by_path.get(target)
                target_title = target_entry["title"] if target_entry else target
                target_link = _wiki_link(target, target_title)
                relation_rows.append((source_link, relation, target_link))

    lines.extend(["## Typed relations", ""])
    if relation_rows:
        lines.append("| From | Relation | To |")
        lines.append("|---|---|---|")
        for source_link, relation, target_link in relation_rows:
            lines.append(f"| {source_link} | `{relation}` | {target_link} |")
    else:
        lines.append("No typed relations are registered.")

    lines.extend(
        [
            "",
            "## Authority boundaries",
            "",
            f"- Registry authority: `{data['authority_scope']}` only.",
            f"- Generation direction: `{data['generation_direction']}` only.",
            "- Research Radar mutable state remains canonical under `docs/research/data/*.json` and is not copied here.",
            "- `docs/research/obsidian/**` and `docs/development/research_radar/**` remain generated Research Radar projections/facades.",
            "- Source documents remain authoritative according to `AGENTS.md`, `docs/ACTIVE_CURRENT.md`, subsystem contracts and live GitHub state.",
            "- Obsidian, Graph, Bases, plugins, search and this index are views/interfaces, not project-state owners.",
            "",
            "## Validation",
            "",
            "Run `python tools/obsidian_knowledge_sync.py --check` to validate the registry and detect generated-index drift.",
            "",
        ]
    )
    return "\n".join(lines)


def build(repo_root: Path, registry_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    data = load_registry(registry_path)
    entries = validate_registry(data, repo_root)
    return data, entries, render_index(data, entries)


def check_index(repo_root: Path, registry_path: Path, output_path: Path) -> tuple[bool, str]:
    _, _, expected = build(repo_root, registry_path)
    try:
        current = output_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, f"generated index missing: {output_path}"
    if current != expected:
        return False, f"generated index is stale: {output_path}"
    return True, "knowledge registry and generated index are valid/current"


def _resolve_repo_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate/generate the Genre_test Obsidian knowledge index.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate and fail if generated output is stale.")
    mode.add_argument("--write", action="store_true", help="Validate then regenerate the derived index.")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    registry_path = _resolve_repo_path(repo_root, args.registry)
    output_path = _resolve_repo_path(repo_root, args.output)

    try:
        if args.write:
            _, _, rendered = build(repo_root, registry_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
            print(f"wrote {output_path.relative_to(repo_root)}")
            return 0

        ok, message = check_index(repo_root, registry_path, output_path)
        print(message)
        return 0 if ok else 1
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
