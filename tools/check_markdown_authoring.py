from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable

SCHEMA = "genre-test-markdown-legacy-baseline-v1"
DEFAULT_BASELINE = Path("docs/obsidian/MARKDOWN_LEGACY_BASELINE.json")
EXPECTED_BASELINE_COMMIT = "107df368fc5fc85f310e84a88a5247e62d1e7c51"
EXPECTED_SCOPE = (
    "AGENTS.md",
    "README.md",
    "README_RUS.md",
    "ROADMAP.md",
    "docs/**/*.md",
)
EXPECTED_EXEMPT_PREFIXES = (
    "docs/development/research_radar/",
    "docs/research/obsidian/",
)
EXPECTED_EXEMPT_PATHS = ("docs/obsidian/KNOWLEDGE_INDEX.md",)

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
REQUIRED_KEYS = {"title", "doc_type", "area", "status", "summary", "tags"}
ROOT_MARKDOWN_SCOPE = {"AGENTS.md", "README.md", "README_RUS.md", "ROADMAP.md"}
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class AuthoringError(ValueError):
    """Raised when the Markdown authoring contract is malformed."""


def _safe_path(raw: str) -> str:
    if not raw or "\\" in raw or "\n" in raw or "\r" in raw:
        raise AuthoringError(f"invalid repository path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise AuthoringError(f"unsafe repository path: {raw!r}")
    return path.as_posix()


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    # Git object identity is SHA-1 by definition; this is not a security digest.
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def load_baseline(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuthoringError(f"baseline manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuthoringError(f"invalid baseline JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise AuthoringError("baseline root must be an object")
    if data.get("schema") != SCHEMA or data.get("schema_version") != 1:
        raise AuthoringError("unsupported baseline schema/version")

    commit = data.get("baseline_commit")
    if commit != EXPECTED_BASELINE_COMMIT:
        raise AuthoringError(
            "baseline_commit does not match the immutable refactor-boundary commit"
        )

    scope = data.get("scope")
    if scope != list(EXPECTED_SCOPE):
        raise AuthoringError("baseline scope differs from the frozen authoring boundary")

    blobs = data.get("baseline_blobs")
    if not isinstance(blobs, dict):
        raise AuthoringError("baseline_blobs must be an object")
    normalized_blobs: dict[str, str] = {}
    for raw_path, sha in blobs.items():
        if not isinstance(raw_path, str) or not isinstance(sha, str):
            raise AuthoringError("baseline_blobs keys/values must be strings")
        repo_path = _safe_path(raw_path)
        if not HEX40_RE.fullmatch(sha):
            raise AuthoringError(f"invalid Git blob SHA for {repo_path}")
        normalized_blobs[repo_path] = sha

    prefixes = data.get("exempt_prefixes", [])
    paths = data.get("exempt_paths", [])
    if prefixes != list(EXPECTED_EXEMPT_PREFIXES):
        raise AuthoringError("exempt_prefixes differ from the frozen authoring boundary")
    if paths != list(EXPECTED_EXEMPT_PATHS):
        raise AuthoringError("exempt_paths differ from the frozen authoring boundary")

    data["baseline_blobs"] = normalized_blobs
    data["exempt_prefixes"] = list(EXPECTED_EXEMPT_PREFIXES)
    data["exempt_paths"] = list(EXPECTED_EXEMPT_PATHS)
    return data


def _in_scope(path: str) -> bool:
    return path in ROOT_MARKDOWN_SCOPE or (path.startswith("docs/") and path.endswith(".md"))


def _is_exempt(path: str, baseline: dict[str, object]) -> bool:
    exempt_paths = set(baseline["exempt_paths"])  # type: ignore[arg-type]
    if path in exempt_paths:
        return True
    return any(path.startswith(prefix) for prefix in baseline["exempt_prefixes"])  # type: ignore[union-attr]


def _git_tree_blobs(repo_root: Path, commit: str) -> dict[str, str]:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", commit],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise AuthoringError(
            f"pinned baseline commit is unavailable to Git: {commit}: {detail}"
        )

    tree: dict[str, str] = {}
    for raw_entry in proc.stdout.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            _mode, object_type, raw_sha = metadata.split(b" ", 2)
            path = raw_path.decode("utf-8")
            sha = raw_sha.decode("ascii")
            kind = object_type.decode("ascii")
        except (UnicodeDecodeError, ValueError) as exc:
            raise AuthoringError("malformed git ls-tree output for baseline commit") from exc
        if kind == "blob":
            tree[_safe_path(path)] = sha
    return tree


def verify_baseline_against_git(
    repo_root: Path,
    baseline: dict[str, object],
) -> None:
    commit = baseline.get("baseline_commit")
    if commit != EXPECTED_BASELINE_COMMIT:
        raise AuthoringError("baseline commit changed after parsing")

    tree = _git_tree_blobs(repo_root.resolve(), EXPECTED_BASELINE_COMMIT)
    expected_paths = {
        path
        for path in tree
        if _in_scope(path) and not _is_exempt(path, baseline)
    }
    blobs = baseline.get("baseline_blobs")
    if not isinstance(blobs, dict):
        raise AuthoringError("normalized baseline_blobs missing")
    recorded_paths = set(blobs)

    missing = sorted(expected_paths - recorded_paths)
    extra = sorted(recorded_paths - expected_paths)
    if missing:
        raise AuthoringError(
            "baseline manifest omits grandfathered paths from pinned commit: "
            + ", ".join(missing)
        )
    if extra:
        raise AuthoringError(
            "baseline manifest records paths outside pinned grandfathering set: "
            + ", ".join(extra)
        )

    mismatches = [
        path
        for path in sorted(expected_paths)
        if blobs.get(path) != tree.get(path)
    ]
    if mismatches:
        raise AuthoringError(
            "baseline blob identities do not match pinned commit: "
            + ", ".join(mismatches)
        )


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_passport(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AuthoringError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AuthoringError("missing closing frontmatter delimiter") from exc
    if end > 80:
        raise AuthoringError("frontmatter is unexpectedly long")

    raw = lines[1:end]
    fields: dict[str, object] = {}
    current_list: str | None = None
    for line in raw:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise AuthoringError("frontmatter list item without a list key")
            value = _unquote(line[4:])
            if not value:
                raise AuthoringError(f"empty list value for {current_list}")
            cast = fields.setdefault(current_list, [])
            if not isinstance(cast, list):
                raise AuthoringError(f"mixed scalar/list field: {current_list}")
            cast.append(value)
            continue

        match = KEY_RE.fullmatch(line)
        if match is None:
            raise AuthoringError(f"unsupported frontmatter syntax: {line!r}")
        key, raw_value = match.groups()
        if key in fields:
            raise AuthoringError(f"duplicate frontmatter key: {key}")
        if raw_value is None or not raw_value.strip():
            fields[key] = []
            current_list = key
        else:
            fields[key] = _unquote(raw_value)
            current_list = None

    missing = REQUIRED_KEYS - fields.keys()
    if missing:
        raise AuthoringError(f"missing passport keys: {', '.join(sorted(missing))}")

    for key in ("title", "doc_type", "area", "status", "summary"):
        if not isinstance(fields[key], str) or not str(fields[key]).strip():
            raise AuthoringError(f"passport field {key} must be a non-empty scalar")

    doc_type = str(fields["doc_type"])
    area = str(fields["area"])
    status = str(fields["status"])
    if doc_type not in DOC_TYPES:
        raise AuthoringError(f"unsupported doc_type: {doc_type}")
    if area not in AREAS:
        raise AuthoringError(f"unsupported area: {area}")
    if status not in STATUSES:
        raise AuthoringError(f"unsupported status: {status}")

    tags = fields["tags"]
    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
        raise AuthoringError("tags must be a non-empty YAML list")
    if len(tags) != len(set(tags)):
        raise AuthoringError("duplicate controlled tags are forbidden")
    expected = {
        f"область/{area}",
        f"тип/{doc_type.replace('_', '-')}",
        f"статус/{status}",
    }
    if set(tags) != expected:
        raise AuthoringError(f"controlled tags mismatch: expected {sorted(expected)!r}")

    body = "\n".join(lines[end + 1 :])
    return fields, body


def validate_structure(body: str) -> list[str]:
    errors: list[str] = []
    headings: list[int] = []
    in_fence = False
    fence_token: str | None = None

    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            token = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_token = token
            elif token == fence_token:
                in_fence = False
                fence_token = None
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append(len(match.group(1)))

    if headings.count(1) != 1:
        errors.append("document must contain exactly one H1")
    if headings and headings[0] != 1:
        errors.append("first heading must be H1")
    for previous, current in zip(headings, headings[1:]):
        if current > previous + 1:
            errors.append(f"heading level skip: H{previous} -> H{current}")
            break
    return errors


def validate_markdown_bytes(data: bytes) -> list[str]:
    errors: list[str] = []
    if b"\r" in data:
        errors.append("new/migrated Markdown must use LF line endings")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return errors + ["Markdown must be UTF-8"]

    try:
        _fields, body = parse_passport(text)
    except AuthoringError as exc:
        return errors + [str(exc)]
    return errors + validate_structure(body)


def _git_tracked_paths(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise AuthoringError(f"git ls-files failed: {detail}")
    return [item for item in proc.stdout.decode("utf-8").split("\0") if item]


def validate_repository(
    repo_root: Path,
    baseline: dict[str, object],
    *,
    tracked_paths: Iterable[str] | None = None,
) -> list[str]:
    root = repo_root.resolve()
    blobs = baseline["baseline_blobs"]
    if not isinstance(blobs, dict):
        raise AuthoringError("normalized baseline_blobs missing")
    paths = list(tracked_paths) if tracked_paths is not None else _git_tracked_paths(root)

    errors: list[str] = []
    for raw_path in sorted(set(paths)):
        path = _safe_path(raw_path)
        if not _in_scope(path) or _is_exempt(path, baseline):
            continue
        full = root.joinpath(*PurePosixPath(path).parts)
        if not full.is_file():
            continue
        data = full.read_bytes()
        baseline_sha = blobs.get(path)
        if isinstance(baseline_sha, str) and _git_blob_sha(data) == baseline_sha:
            continue

        file_errors = validate_markdown_bytes(data)
        errors.extend(f"{path}: {error}" for error in file_errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Genre_test Markdown authoring boundary")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    baseline_path = args.baseline
    if not baseline_path.is_absolute():
        baseline_path = repo_root / baseline_path

    try:
        baseline = load_baseline(baseline_path)
        verify_baseline_against_git(repo_root, baseline)
        errors = validate_repository(repo_root, baseline)
    except AuthoringError as exc:
        print(f"Markdown authoring check ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("Markdown authoring check FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Markdown authoring check PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
