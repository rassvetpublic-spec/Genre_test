from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "genre-test-obsidian-knowledge-registry-v1"
AUTHORITY_SCOPE = "knowledge_navigation_metadata_only"
GENERATION_DIRECTION = "JSON_TO_MARKDOWN"
INVENTORY_SCHEMA = "genre-test-repository-inventory-v1"
INVENTORY_AUTHORITY = "derived_projection_only"
BASELINE_SCHEMA = "genre-test-markdown-legacy-baseline-v1"
BASELINE_COMMIT = "107df368fc5fc85f310e84a88a5247e62d1e7c51"

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
    | {"reader_level", "language"}
)
ALLOWED_ROOT_KEYS = {
    "schema",
    "schema_version",
    "authority_scope",
    "generation_direction",
    "entries",
}
OWNERSHIP_CLASSES = {
    "canonical_document",
    "canonical_machine_state",
    "generated_projection",
    "derived_index",
    "visualization",
}

DEFAULT_REGISTRY = Path("docs/obsidian/KNOWLEDGE_REGISTRY.json")
DEFAULT_OUTPUT = Path("docs/obsidian/KNOWLEDGE_INDEX.md")
DEFAULT_BASELINE = Path("docs/obsidian/MARKDOWN_LEGACY_BASELINE.json")
DEFAULT_INVENTORY = Path("docs/obsidian/REPOSITORY_INVENTORY.json")
DEFAULT_HOME = Path("docs/obsidian/HOME.md")
DEFAULT_ANALYTICS = Path("docs/obsidian/KNOWLEDGE_ANALYTICS.md")
DEFAULT_KNOWLEDGE_BASE = Path("docs/obsidian/KNOWLEDGE.base")
DEFAULT_RELATIONS_BASE = Path("docs/obsidian/RELATIONS.base")
DEFAULT_TERMS_BASE = Path("docs/obsidian/TERMS.base")

REGISTRY_SELF_PATH = DEFAULT_REGISTRY.as_posix()
GENERATED_INDEX_PATH = DEFAULT_OUTPUT.as_posix()
BASELINE_PATH = DEFAULT_BASELINE.as_posix()
GLOBAL_GENERATED_MARKDOWN = {
    GENERATED_INDEX_PATH,
    DEFAULT_HOME.as_posix(),
    DEFAULT_ANALYTICS.as_posix(),
}
GLOBAL_GENERATED_OUTPUTS = {
    *GLOBAL_GENERATED_MARKDOWN,
    DEFAULT_INVENTORY.as_posix(),
    DEFAULT_KNOWLEDGE_BASE.as_posix(),
    DEFAULT_RELATIONS_BASE.as_posix(),
    DEFAULT_TERMS_BASE.as_posix(),
}
FORBIDDEN_RADAR_PREFIXES = (
    "docs/research/data/",
    "docs/research/obsidian/",
    "docs/development/research_radar/",
)
RADAR_MACHINE_PREFIX = "docs/research/data/"
RADAR_GENERATED_PREFIXES = (
    "docs/research/obsidian/",
    "docs/development/research_radar/",
)
ROOT_MARKDOWN_SCOPE = {"AGENTS.md", "README.md", "README_RUS.md", "ROADMAP.md"}


class RegistryError(ValueError):
    """Raised when the knowledge/projection contract is malformed."""


def _safe_repo_path(raw: Any, *, field: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw.strip():
        raise RegistryError(f"{field}: expected a non-empty repository-relative path")
    if "\\" in raw:
        raise RegistryError(f"{field}: use forward slashes in repository paths: {raw!r}")
    if "\n" in raw or "\r" in raw:
        raise RegistryError(f"{field}: CR/LF forbidden in repository paths")
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("/") or ".." in path.parts:
        raise RegistryError(f"{field}: path traversal/absolute path is forbidden: {raw!r}")
    if any(part in {"", "."} for part in path.parts):
        raise RegistryError(f"{field}: non-normalized path is forbidden: {raw!r}")
    return path


def _resolved_inside_repo(repo_root: Path, path: Path, *, field: str) -> Path:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RegistryError(f"{field}: resolved path escapes repository root: {path}") from exc
    return resolved_path


def _fixed_repo_path(repo_root: Path, relative_path: Path, *, field: str) -> Path:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise RegistryError(f"{field}: fixed path must remain repository-relative")
    resolved_root = repo_root.resolve()
    current = resolved_root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise RegistryError(f"{field}: symlinked path component is forbidden: {current}")
    resolved = _resolved_inside_repo(resolved_root, current, field=field)
    if resolved != current:
        raise RegistryError(f"{field}: canonical path resolves to a different location: {current}")
    return current


def _existing_repo_file(repo_root: Path, rel_path: PurePosixPath, *, field: str) -> Path:
    candidate = repo_root.joinpath(*rel_path.parts)
    resolved = _resolved_inside_repo(repo_root, candidate, field=field)
    if not resolved.is_file():
        raise RegistryError(f"{field}: referenced file does not exist: {rel_path.as_posix()}")
    return resolved


def _atomic_write_text(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, output_path)
        temp_path = None
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _require_string(entry: dict[str, Any], key: str, label: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{label}.{key}: expected a non-empty string")
    if "\n" in value or "\r" in value:
        raise RegistryError(f"{label}.{key}: line breaks are forbidden in single-line string fields")
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


def load_authoring_boundary(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"authoring boundary not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryError(f"invalid authoring boundary JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError("authoring boundary root must be an object")
    if data.get("schema") != BASELINE_SCHEMA or data.get("schema_version") != 1:
        raise RegistryError("unsupported Markdown authoring boundary schema/version")
    if data.get("baseline_commit") != BASELINE_COMMIT:
        raise RegistryError("Markdown authoring boundary commit changed")
    blobs = data.get("baseline_blobs")
    if not isinstance(blobs, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in blobs.items()
    ):
        raise RegistryError("authoring boundary baseline_blobs must be a string mapping")
    for key in ("exempt_prefixes", "exempt_paths"):
        value = data.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise RegistryError(f"authoring boundary {key} must be a string list")
    return data


def _validate_supersession_graph(entries: list[dict[str, Any]]) -> None:
    graph: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        source = entry["path"]
        for target in entry.get("supersedes", []):
            graph[source].add(target)
        for successor in entry.get("superseded_by", []):
            graph[successor].add(source)
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle_start = stack.index(node)
            cycle = stack[cycle_start:] + [node]
            raise RegistryError(f"supersession cycle is forbidden: {' -> '.join(cycle)}")
        visiting.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, set())):
            visit(target)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)


def validate_registry(data: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    unknown_root = sorted(set(data) - ALLOWED_ROOT_KEYS)
    if unknown_root:
        raise RegistryError(f"unapproved registry root keys: {', '.join(unknown_root)}")
    missing_root = sorted(ALLOWED_ROOT_KEYS - set(data))
    if missing_root:
        raise RegistryError(f"missing registry root keys: {', '.join(missing_root)}")
    if data.get("schema") != SCHEMA:
        raise RegistryError(f"schema must be {SCHEMA!r}")
    if data.get("schema_version") != 1:
        raise RegistryError("schema_version must be 1")
    if data.get("authority_scope") != AUTHORITY_SCOPE:
        raise RegistryError(f"authority_scope must be {AUTHORITY_SCOPE!r}")
    if data.get("generation_direction") != GENERATION_DIRECTION:
        raise RegistryError(f"generation_direction must be {GENERATION_DIRECTION!r}")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RegistryError("entries must be a non-empty list")
    seen_paths: set[str] = set()
    normalized_entries: list[dict[str, Any]] = []

    for index, raw_entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(raw_entry, dict):
            raise RegistryError(f"{label}: entry must be an object")
        missing = sorted(REQUIRED_ENTRY_KEYS - raw_entry.keys())
        if missing:
            raise RegistryError(f"{label}: missing required keys: {', '.join(missing)}")
        unknown = sorted(set(raw_entry) - ALLOWED_ENTRY_KEYS)
        if unknown:
            raise RegistryError(f"{label}: unapproved metadata keys: {', '.join(unknown)}")

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
        _existing_repo_file(repo_root, rel_path, field=f"{label}.path")

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
                _existing_repo_file(repo_root, target_path, field=f"{label}.{relation}[{target_index}]")
                if target_text == path_text:
                    raise RegistryError(f"{label}.{relation}: self-reference is forbidden: {path_text}")
                normalized_targets.append(target_text)
            normalized[relation] = normalized_targets
        normalized_entries.append(normalized)

    _validate_supersession_graph(normalized_entries)
    return normalized_entries


def _wiki_target(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _wiki_link(path: str, title: str) -> str:
    safe_title = title.replace("|", "-")
    return f"[[{_wiki_target(path)}|{safe_title}]]"


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def tracked_worktree_blobs(repo_root: Path) -> dict[str, str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RegistryError(f"git ls-files failed: {detail}")
    result: dict[str, str] = {}
    for raw_path in proc.stdout.split(b"\0"):
        if not raw_path:
            continue
        try:
            path = raw_path.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RegistryError("tracked path is not UTF-8") from exc
        safe = _safe_repo_path(path, field="git tracked path").as_posix()
        candidate = repo_root.joinpath(*PurePosixPath(safe).parts)
        if not candidate.is_file():
            continue
        result[safe] = _git_blob_sha(candidate.read_bytes())
    return result


def _in_authoring_scope(path: str) -> bool:
    return path in ROOT_MARKDOWN_SCOPE or (path.startswith("docs/") and path.endswith(".md"))


def _boundary_exempt(path: str, boundary: dict[str, Any]) -> bool:
    if path in set(boundary.get("exempt_paths", [])):
        return True
    return any(path.startswith(prefix) for prefix in boundary.get("exempt_prefixes", []))


def registration_state(
    path: str,
    blob_sha: str,
    boundary: dict[str, Any],
    registered_paths: set[str],
) -> str:
    if path in GLOBAL_GENERATED_MARKDOWN:
        return "generated_view"
    if not _in_authoring_scope(path) or _boundary_exempt(path, boundary):
        return "exempt"
    baseline = boundary["baseline_blobs"]
    if path in registered_paths:
        return "registered"
    if baseline.get(path) == blob_sha:
        return "grandfathered"
    return "registration_required"


def _is_inventory_relevant(path: str, registered_paths: set[str]) -> bool:
    if path in registered_paths or path in {REGISTRY_SELF_PATH, BASELINE_PATH}:
        return True
    if path in GLOBAL_GENERATED_OUTPUTS:
        return True
    if _in_authoring_scope(path):
        return True
    if path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json"):
        return True
    if any(path.startswith(prefix) for prefix in RADAR_GENERATED_PREFIXES):
        return path.endswith((".md", ".json", ".yaml", ".yml"))
    return False


def _ownership_class(path: str) -> str:
    if path in {REGISTRY_SELF_PATH, BASELINE_PATH} or (
        path.startswith(RADAR_MACHINE_PREFIX) and path.endswith(".json")
    ):
        return "canonical_machine_state"
    if path in {
        DEFAULT_OUTPUT.as_posix(),
        DEFAULT_HOME.as_posix(),
        DEFAULT_ANALYTICS.as_posix(),
        DEFAULT_INVENTORY.as_posix(),
    }:
        return "derived_index"
    if path in {
        DEFAULT_KNOWLEDGE_BASE.as_posix(),
        DEFAULT_RELATIONS_BASE.as_posix(),
        DEFAULT_TERMS_BASE.as_posix(),
    }:
        return "visualization"
    if any(path.startswith(prefix) for prefix in RADAR_GENERATED_PREFIXES):
        return "generated_projection"
    return "canonical_document"


def _source_fingerprint(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"genre-test-obsidian-projection-input-v1\0")
    for record in records:
        if record["path"] in GLOBAL_GENERATED_OUTPUTS:
            continue
        digest.update(record["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(record["ownership_class"].encode("ascii"))
        digest.update(b"\0")
        blob = record.get("blob_sha")
        if record["ownership_class"] in {"generated_projection", "visualization", "derived_index"}:
            blob = None
        digest.update((blob or "path-only").encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def build_inventory(
    tracked_blobs: dict[str, str],
    entries: list[dict[str, Any]],
    boundary: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    by_path = {entry["path"]: entry for entry in entries}
    registered_paths = set(by_path)
    paths = {
        path for path in tracked_blobs if _is_inventory_relevant(path, registered_paths)
    } | GLOBAL_GENERATED_OUTPUTS
    records: list[dict[str, Any]] = []
    missing_registration: list[str] = []
    for path in sorted(paths):
        ownership_class = _ownership_class(path)
        if ownership_class not in OWNERSHIP_CLASSES:
            raise RegistryError(f"unsupported ownership class for {path}: {ownership_class}")
        blob_sha = None if path in GLOBAL_GENERATED_OUTPUTS else tracked_blobs.get(path)
        state = "not_applicable"
        if path.endswith(".md") and blob_sha is not None:
            state = registration_state(path, blob_sha, boundary, registered_paths)
            if state == "registration_required":
                missing_registration.append(path)
        record: dict[str, Any] = {
            "path": path,
            "ownership_class": ownership_class,
            "registration_state": state,
            "blob_sha": blob_sha,
        }
        if path in by_path:
            record.update(
                {
                    "area": by_path[path]["area"],
                    "doc_type": by_path[path]["doc_type"],
                    "status": by_path[path]["status"],
                }
            )
        records.append(record)
    fingerprint = _source_fingerprint(records)
    counts = Counter(record["ownership_class"] for record in records)
    registration_counts = Counter(record["registration_state"] for record in records)
    inventory = {
        "schema": INVENTORY_SCHEMA,
        "schema_version": 1,
        "authority_scope": INVENTORY_AUTHORITY,
        "generation_direction": "REPOSITORY_TO_DERIVED_JSON",
        "source_fingerprint": fingerprint,
        "canonical_inputs": {
            "knowledge_registry": REGISTRY_SELF_PATH,
            "markdown_boundary": BASELINE_PATH,
            "research_machine_state_prefix": RADAR_MACHINE_PREFIX,
        },
        "excluded_from_authority": [
            "GitHub live Issue/PR/check state",
            "local .obsidian state",
            "audio/renders/model weights/caches",
        ],
        "counts": dict(sorted(counts.items())),
        "registration_counts": dict(sorted(registration_counts.items())),
        "entries": records,
    }
    return inventory, missing_registration


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
        "Registration is now enforced for new or materially migrated human Markdown; unchanged grandfathered documents may remain outside the principal registry.",
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
                relation_rows.append((source_link, relation, _wiki_link(target, target_title)))
    lines.extend(["## Typed relations", ""])
    if relation_rows:
        lines.extend(["| From | Relation | To |", "|---|---|---|"])
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
            "- Obsidian HOME, Bases, analytics, Graph and this index are derived views, not project-state owners.",
            "",
            "## Validation",
            "",
            "Run `python tools/obsidian_knowledge_sync.py --check` to validate all Obsidian repository projections and registration drift.",
            "",
        ]
    )
    return "\n".join(lines)


def render_home(entries: list[dict[str, Any]], inventory: dict[str, Any]) -> str:
    by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_area[entry["area"]].append(entry)
    lines = [
        "---",
        'title: "Genre_test Knowledge Home"',
        "doc_type: index",
        "area: project",
        "status: generated",
        'summary: "Generated repository-native Obsidian HOME linking canonical owners and deterministic knowledge views."',
        "tags:",
        "  - область/project",
        "  - тип/index",
        "  - статус/generated",
        "generated: true",
        f'canonical_owner: "{REGISTRY_SELF_PATH}"',
        "---",
        "",
        "# Genre_test Knowledge Home",
        "",
        "<!-- GENERATED BY tools/obsidian_knowledge_sync.py; DO NOT EDIT BY HAND -->",
        "",
        "> Navigation only. Git/repository owners remain authoritative; live GitHub state must be read from GitHub rather than copied here.",
        "",
        "## Core entry points",
        "",
    ]
    preferred = [
        "README.md",
        "AGENTS.md",
        "docs/ACTIVE_CURRENT.md",
        "ROADMAP.md",
        "docs/REPOSITORY_COLD_START.md",
        "docs/SUPERCOMBINE_UI_ARCHITECTURE.md",
        "docs/obsidian/MARKDOWN_AUTHORING_STANDARD.md",
    ]
    by_path = {entry["path"]: entry for entry in entries}
    for path in preferred:
        entry = by_path.get(path)
        if entry:
            lines.append(f"- {_wiki_link(path, entry['title'])} — {entry['summary']}")
    lines.extend(["", "## Areas", ""])
    for area in sorted(by_area):
        lines.append(f"### `{area}`")
        lines.append("")
        for entry in sorted(by_area[area], key=lambda item: (item["status"], item["title"].casefold())):
            lines.append(f"- {_wiki_link(entry['path'], entry['title'])} (`{entry['status']}` / `{entry['doc_type']}`)")
        lines.append("")
    lines.extend(
        [
            "## Derived views",
            "",
            f"- [[{_wiki_target(DEFAULT_OUTPUT.as_posix())}|Knowledge Index]]",
            f"- [[{_wiki_target(DEFAULT_ANALYTICS.as_posix())}|Knowledge Analytics]]",
            f"- `{DEFAULT_INVENTORY.as_posix()}` — machine-readable repository inventory.",
            f"- `{DEFAULT_KNOWLEDGE_BASE.as_posix()}` — native Base: documents by area/type/status.",
            f"- `{DEFAULT_RELATIONS_BASE.as_posix()}` — native Base: typed relations.",
            f"- `{DEFAULT_TERMS_BASE.as_posix()}` — native Base: terms and local discovery keywords.",
            "",
            "## Projection identity",
            "",
            f"Source fingerprint: `{inventory['source_fingerprint']}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_analytics(
    entries: list[dict[str, Any]],
    inventory: dict[str, Any],
    missing_registration: list[str],
) -> str:
    tags = Counter(tag for entry in entries for tag in entry.get("tags", []))
    terms = Counter(term for entry in entries for term in entry.get("terms", []))
    keywords_ru = Counter(word for entry in entries for word in entry.get("keywords_ru", []))
    keywords_en = Counter(word for entry in entries for word in entry.get("keywords_en", []))
    relations = Counter(
        relation
        for entry in entries
        for relation in RELATION_KEYS
        for _target in entry.get(relation, [])
    )
    referenced = {
        target
        for entry in entries
        for relation in RELATION_KEYS
        for target in entry.get(relation, [])
    }
    orphans = sorted(entry["path"] for entry in entries if not any(entry.get(key) for key in RELATION_KEYS) and entry["path"] not in referenced)
    lines = [
        "---",
        'title: "Genre_test Knowledge Analytics"',
        "doc_type: index",
        "area: project",
        "status: generated",
        'summary: "Deterministic tag, term, relation and registration diagnostics for the repository-native Obsidian layer."',
        "tags:",
        "  - область/project",
        "  - тип/index",
        "  - статус/generated",
        "generated: true",
        f'canonical_owner: "{REGISTRY_SELF_PATH}"',
        "---",
        "",
        "# Genre_test Knowledge Analytics",
        "",
        "<!-- GENERATED BY tools/obsidian_knowledge_sync.py; DO NOT EDIT BY HAND -->",
        "",
        f"Source fingerprint: `{inventory['source_fingerprint']}`",
        "",
        "## Registration gate",
        "",
        f"- Registered principal documents: **{len(entries)}**",
        f"- Registration-required but missing: **{len(missing_registration)}**",
    ]
    if missing_registration:
        for path in missing_registration:
            lines.append(f"  - `{path}`")
    lines.extend(["", "## Controlled tags", "", "| Tag | Count |", "|---|---:|"])
    for value, count in sorted(tags.items()):
        lines.append(f"| `{value}` | {count} |")
    lines.extend(["", "## Typed relations", "", "| Relation | Count |", "|---|---:|"])
    for relation in sorted(RELATION_KEYS):
        lines.append(f"| `{relation}` | {relations[relation]} |")
    lines.extend(["", "## Terms", "", "| Term | Documents |", "|---|---:|"])
    for value, count in sorted(terms.items(), key=lambda item: (-item[1], item[0].casefold())):
        lines.append(f"| {value.replace('|', '\\|')} | {count} |")
    if keywords_ru or keywords_en:
        lines.extend(["", "## Local discovery keywords", ""])
        for label, counter in (("RU", keywords_ru), ("EN", keywords_en)):
            if counter:
                lines.extend([f"### {label}", "", "| Keyword | Documents |", "|---|---:|"])
                for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0].casefold())):
                    lines.append(f"| {value.replace('|', '\\|')} | {count} |")
                lines.append("")
    lines.extend(["## Relation coverage diagnostics", "", f"Registered documents with no registry relation edge: **{len(orphans)}**.", ""])
    for path in orphans:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Ownership classes",
            "",
            "| Class | Files |",
            "|---|---:|",
        ]
    )
    for key, count in sorted(inventory["counts"].items()):
        lines.append(f"| `{key}` | {count} |")
    lines.append("")
    return "\n".join(lines)


def render_knowledge_base() -> str:
    return """filters:\n  and:\n    - 'file.ext == "md"'\n    - 'doc_type != null'\nproperties:\n  file.name:\n    displayName: File\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  doc_type:\n    displayName: Type\n  status:\n    displayName: Status\n  summary:\n    displayName: Summary\nviews:\n  - type: table\n    name: By area\n    order:\n      - title\n      - doc_type\n      - status\n      - summary\n    groupBy:\n      property: area\n      direction: ASC\n  - type: table\n    name: By type\n    order:\n      - title\n      - area\n      - status\n    groupBy:\n      property: doc_type\n      direction: ASC\n  - type: table\n    name: By status\n    order:\n      - title\n      - area\n      - doc_type\n    groupBy:\n      property: status\n      direction: ASC\n"""


def render_relations_base() -> str:
    relation_filter = "\n".join(f"        - '{key} != null'" for key in sorted(RELATION_KEYS))
    order = "\n".join(f"      - {key}" for key in sorted(RELATION_KEYS))
    return f"""filters:\n  and:\n    - 'file.ext == "md"'\n    - or:\n{relation_filter}\nproperties:\n  file.name:\n    displayName: File\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  doc_type:\n    displayName: Type\nviews:\n  - type: table\n    name: Typed relations\n    order:\n      - title\n      - area\n      - doc_type\n{order}\n    groupBy:\n      property: area\n      direction: ASC\n"""


def render_terms_base() -> str:
    return """filters:\n  and:\n    - 'file.ext == "md"'\n    - or:\n        - 'terms != null'\n        - 'keywords_ru != null'\n        - 'keywords_en != null'\nproperties:\n  file.name:\n    displayName: File\n  title:\n    displayName: Title\n  area:\n    displayName: Area\n  terms:\n    displayName: Terms\n  keywords_ru:\n    displayName: Keywords RU\n  keywords_en:\n    displayName: Keywords EN\nviews:\n  - type: table\n    name: Terms and keywords\n    order:\n      - title\n      - area\n      - terms\n      - keywords_ru\n      - keywords_en\n    groupBy:\n      property: area\n      direction: ASC\n"""


def build_projections(
    repo_root: Path,
    registry_path: Path,
    boundary_path: Path,
    *,
    tracked_blobs: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
    data = load_registry(registry_path)
    entries = validate_registry(data, repo_root)
    boundary = load_authoring_boundary(boundary_path)
    blobs = tracked_blobs if tracked_blobs is not None else tracked_worktree_blobs(repo_root)
    inventory, missing_registration = build_inventory(blobs, entries, boundary)
    if missing_registration:
        raise RegistryError(
            "registration-required Markdown is absent from KNOWLEDGE_REGISTRY.json: "
            + ", ".join(missing_registration)
        )
    outputs = {
        DEFAULT_OUTPUT.as_posix(): render_index(data, entries),
        DEFAULT_INVENTORY.as_posix(): json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        DEFAULT_HOME.as_posix(): render_home(entries, inventory),
        DEFAULT_ANALYTICS.as_posix(): render_analytics(entries, inventory, missing_registration),
        DEFAULT_KNOWLEDGE_BASE.as_posix(): render_knowledge_base(),
        DEFAULT_RELATIONS_BASE.as_posix(): render_relations_base(),
        DEFAULT_TERMS_BASE.as_posix(): render_terms_base(),
    }
    return data, entries, outputs, missing_registration


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


def check_all(repo_root: Path) -> tuple[bool, str]:
    registry_path = _fixed_repo_path(repo_root, DEFAULT_REGISTRY, field="registry")
    boundary_path = _fixed_repo_path(repo_root, DEFAULT_BASELINE, field="Markdown boundary")
    _, _, outputs, _ = build_projections(repo_root, registry_path, boundary_path)
    stale: list[str] = []
    for relative, expected in outputs.items():
        path = _fixed_repo_path(repo_root, Path(relative), field=f"generated output {relative}")
        try:
            current = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            stale.append(f"missing:{relative}")
            continue
        if current != expected:
            stale.append(f"stale:{relative}")
    if stale:
        return False, "Obsidian projection drift: " + ", ".join(stale)
    return True, "Obsidian registry, inventory, HOME, analytics, Bases and registration gate are current"


def write_all(repo_root: Path) -> None:
    registry_path = _fixed_repo_path(repo_root, DEFAULT_REGISTRY, field="registry")
    boundary_path = _fixed_repo_path(repo_root, DEFAULT_BASELINE, field="Markdown boundary")
    _, _, outputs, _ = build_projections(repo_root, registry_path, boundary_path)
    for relative, content in outputs.items():
        path = _fixed_repo_path(repo_root, Path(relative), field=f"generated output {relative}")
        _atomic_write_text(path, content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate/generate the Genre_test repository-native Obsidian knowledge projections."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Explicit repository root; registry/output locations remain fixed inside this root.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate and fail if any projection/registration state is stale.")
    mode.add_argument("--write", action="store_true", help="Validate then regenerate all derived Obsidian projections.")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    try:
        if args.write:
            write_all(repo_root)
            print("wrote Obsidian repository inventory, HOME, analytics, Bases and Knowledge Index")
            return 0
        ok, message = check_all(repo_root)
        print(message)
        return 0 if ok else 1
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
