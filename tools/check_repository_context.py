from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


ACTIVE_REQUIRED = (
    "Published stable version: **none**",
    "standing automatic MTD authorization",
    "docs/REPOSITORY_COLD_START.md",
    "#27 runtime compatibility/isolation** — completed",
)

ACTIVE_FORBIDDEN = (
    "Current first implementation issue: **#27**",
    "currently in **compatibility-spike** phase (#27)",
    r"releases\Genre_test_0.4.0_portable.zip",
    r"releases\SHA256SUMS.txt",
    "No v0.5 feature PR is merged to `main` until explicit MTD",
    "no future repair/master/tag/runtime feature is merged without explicit MTD",
    ".genre_test/retrieval/",
)

ARCH_REQUIRED = (
    "# ARCHITECTURE — current system map",
    "## 1. Core Analysis / Profile",
    "## 2. Retrieval / Catalog / Search",
    "## 3. Shared Technical QC / marker layer",
    "## 4. Repair / Stem / Vocal processing",
    "## 5. Ozone 12 / REAPER mastering",
    "## 6. Synchronized A/B/X review",
    "## 7. Metadata, asset lineage and delivery",
    "## 8. Runtime / ComfyUI / automation",
    "## 9. Agent governance and repository workflow",
    "docs/REPOSITORY_COLD_START.md",
)

ARCH_FORBIDDEN = (
    "# ARCHITECTURE — v0.4.0",
    "Shared MAEST/AST decode/cache is planned for v0.4.1",
)

COLD_START_REQUIRED = (
    "# Repository cold-start recovery contract",
    "CURRENT VERSION",
    "CURRENT MILESTONE",
    "CURRENT ARCHITECTURE",
    "PROTECTED BASELINES",
    "ASSIGNED ISSUE / TASK CONTRACT",
    "NEXT ALLOWED ACTION",
    "Live-state rule",
    "Conflict policy",
    "Cold-start acceptance test",
)

ROADMAP_REQUIRED = (
    "selected isolated persistent Python 3.12 CLaMP 3 sidecar runtime (#27 complete)",
    "#27 is complete:** the selected v0.5 architecture is an isolated persistent Python 3.12 subprocess sidecar",
)

ROADMAP_FORBIDDEN = (
    "isolated optional CLaMP 3 runtime until compatibility is proven",
    "Initial work therefore assumes an isolated subprocess sidecar until #27 proves whether safer consolidation is possible",
)

THIRD_PARTY_REQUIRED = (
    "#27-selected isolated persistent Python 3.12 sidecar",
)

THIRD_PARTY_FORBIDDEN = (
    "keep them in the isolated Python 3.12 sidecar until #27 proves a safer consolidation route",
)

CLAMP_ARCH_REQUIRED = (
    "Runtime decision: **#27 complete**",
    "Selected v0.5 design after #27 compatibility/isolation work:",
    "persistent isolated CLaMP sidecar runtime",
    "Python 3.12 / upstream-compatible dependency stack",
)

CLAMP_ARCH_FORBIDDEN = (
    "Preferred provisional design while #27 is open:",
    "The sidecar decision is provisional until compatibility measurements in #27 are complete.",
)

RETRIEVAL_ACCEPTANCE_REQUIRED = (
    "READY-MTD <exact-head-sha>",
    "standing automatic MTD authorization",
)

RETRIEVAL_ACCEPTANCE_FORBIDDEN = (
    "The code block can be merged only after CI is green and explicit MTD.",
)

CLAMP_RUNTIME_REQUIRED = (
    "Issue: **#27 — COMPLETED**",
    "Status: **runtime decision completed and merged via PR #72 on 2026-08-27**",
    "clamp3-mert-24k-mono-scipy-polyphase-5s-mean-v3",
    "standing automatic MTD authorization",
)

CLAMP_RUNTIME_FORBIDDEN = (
    "Status: **hardware validation in progress on PR #72**",
    "PR merge only after explicit MTD.",
)

CLAMP_P0_REQUIRED = (
    "Status: **hardware acceptance PASS; PR #72 merged on 2026-08-27 under authorized MTD**.",
    "isolated persistent CLaMP 3 SAAS sidecar with corrected MERT v3 preprocessing identity",
    "standing automatic MTD authorization",
)

CLAMP_P0_FORBIDDEN = (
    "Status: **hardware acceptance PASS on PR #72; merge still requires explicit MTD**.",
    "PR #72 and the issue implementation state must remain unmerged/open until the user gives explicit **MTD**.",
)

AGENTS_REQUIRED = (
    "standing automatic MTD authorization",
    "current `Genre_test/main` contracts take precedence",
    "A new repository-aware agent must recover state from repository/GitHub evidence rather than chat memory",
)

_VERSION_PATTERN = re.compile(r"Active development version: \*\*([^*]+)\*\*")
_ROADMAP_VERSION_PATTERN = re.compile(
    r"(?m)^\*\*([^*\n]+) — active development; no packaged stable release is currently published\*\*$"
)


def read_project_version(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml must define a non-empty [project].version")
    return version.strip()


def _check_required(label: str, text: str, markers: tuple[str, ...]) -> list[str]:
    return [
        f"{label}: missing required marker: {marker}"
        for marker in markers
        if marker not in text
    ]


def _check_forbidden(label: str, text: str, markers: tuple[str, ...]) -> list[str]:
    return [
        f"{label}: obsolete/forbidden marker present: {marker}"
        for marker in markers
        if marker in text
    ]


def _markdown_section(text: str, heading: str) -> str:
    start_marker = f"## {heading}"
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    match = re.search(r"(?m)^## ", text[start:])
    end = start + match.start() if match else len(text)
    return text[start:end]


def _numbered_steps(text: str, heading: str) -> list[str]:
    section = _markdown_section(text, heading)
    return re.findall(r"(?m)^\d+\.\s+.+$", section)


def _recovery_step_key(step: str) -> str | None:
    lower = step.lower()
    if "`agents.md`" in lower:
        return "agents"
    if "`docs/active_current.md`" in lower:
        return "active_current"
    if "`roadmap.md`" in lower:
        return "roadmap"
    if "github issue" in lower:
        return "issue_state"
    if "architecture/contracts" in lower or "architecture.md" in lower:
        return "architecture"
    if "nearby implementation" in lower:
        return "implementation_tests"
    if "required review/evidence" in lower:
        return "review_evidence"
    if "next permitted" in lower or "agent_workflow.md" in lower:
        return "next_transition"
    return None


def _check_recovery_order(cold_start: str, agents: str) -> list[str]:
    authoritative_steps = _numbered_steps(agents, "Repository-native context")
    cold_steps = _numbered_steps(cold_start, "Required recovery order")
    if not authoritative_steps:
        return ["AGENTS: repository-native recovery list is missing"]
    if not cold_steps:
        return ["REPOSITORY_COLD_START: required recovery list is missing"]

    authoritative_keys = [_recovery_step_key(step) for step in authoritative_steps]
    cold_keys = [_recovery_step_key(step) for step in cold_steps]
    if any(key is None for key in authoritative_keys):
        return ["AGENTS: repository-native recovery list contains an unrecognized step"]
    if any(key is None for key in cold_keys):
        return ["REPOSITORY_COLD_START: recovery list contains an unrecognized step"]
    if len(set(authoritative_keys)) != len(authoritative_keys):
        return ["AGENTS: repository-native recovery list contains duplicate semantic steps"]
    if len(set(cold_keys)) != len(cold_keys):
        return ["REPOSITORY_COLD_START: recovery list contains duplicate semantic steps"]
    if cold_keys != authoritative_keys:
        return ["REPOSITORY_COLD_START: required recovery order is inconsistent with AGENTS.md"]
    return []


def _check_version(label: str, text: str, expected_version: str) -> list[str]:
    marker = f"Active development version: **{expected_version}**"
    errors = _check_required(label, text, (marker,))
    found = _VERSION_PATTERN.findall(text)
    wrong = sorted({version for version in found if version != expected_version})
    errors.extend(
        f"{label}: stale active development version {version}; expected {expected_version}"
        for version in wrong
    )
    return errors


def _check_roadmap_version(roadmap: str, expected_version: str) -> list[str]:
    found = _ROADMAP_VERSION_PATTERN.findall(roadmap)
    if not found:
        return ["ROADMAP: current development version declaration is missing"]
    wrong = sorted({version.strip() for version in found if version.strip() != expected_version})
    if wrong:
        return [
            f"ROADMAP: stale current development version {version}; expected {expected_version}"
            for version in wrong
        ]
    return []


def validate_texts(
    *,
    active: str,
    architecture: str,
    cold_start: str,
    roadmap: str,
    third_party: str,
    clamp_architecture: str,
    retrieval_acceptance: str,
    clamp_runtime: str,
    clamp_runtime_p0: str,
    agents: str,
    expected_version: str,
) -> list[str]:
    errors: list[str] = []
    errors.extend(_check_version("ACTIVE_CURRENT", active, expected_version))
    errors.extend(_check_required("ACTIVE_CURRENT", active, ACTIVE_REQUIRED))
    errors.extend(_check_forbidden("ACTIVE_CURRENT", active, ACTIVE_FORBIDDEN))
    errors.extend(_check_version("ARCHITECTURE", architecture, expected_version))
    errors.extend(_check_required("ARCHITECTURE", architecture, ARCH_REQUIRED))
    errors.extend(_check_forbidden("ARCHITECTURE", architecture, ARCH_FORBIDDEN))
    errors.extend(_check_required("REPOSITORY_COLD_START", cold_start, COLD_START_REQUIRED))
    errors.extend(_check_recovery_order(cold_start, agents))
    errors.extend(_check_roadmap_version(roadmap, expected_version))
    errors.extend(_check_required("ROADMAP", roadmap, ROADMAP_REQUIRED))
    errors.extend(_check_forbidden("ROADMAP", roadmap, ROADMAP_FORBIDDEN))
    errors.extend(_check_required("THIRD_PARTY_MODELS", third_party, THIRD_PARTY_REQUIRED))
    errors.extend(_check_forbidden("THIRD_PARTY_MODELS", third_party, THIRD_PARTY_FORBIDDEN))
    errors.extend(_check_required("CLAMP3_ARCHITECTURE", clamp_architecture, CLAMP_ARCH_REQUIRED))
    errors.extend(_check_forbidden("CLAMP3_ARCHITECTURE", clamp_architecture, CLAMP_ARCH_FORBIDDEN))
    errors.extend(
        _check_required(
            "CLAMP3_RETRIEVAL_ACCEPTANCE",
            retrieval_acceptance,
            RETRIEVAL_ACCEPTANCE_REQUIRED,
        )
    )
    errors.extend(
        _check_forbidden(
            "CLAMP3_RETRIEVAL_ACCEPTANCE",
            retrieval_acceptance,
            RETRIEVAL_ACCEPTANCE_FORBIDDEN,
        )
    )
    errors.extend(_check_required("CLAMP3_RUNTIME", clamp_runtime, CLAMP_RUNTIME_REQUIRED))
    errors.extend(_check_forbidden("CLAMP3_RUNTIME", clamp_runtime, CLAMP_RUNTIME_FORBIDDEN))
    errors.extend(_check_required("CLAMP3_RUNTIME_P0", clamp_runtime_p0, CLAMP_P0_REQUIRED))
    errors.extend(_check_forbidden("CLAMP3_RUNTIME_P0", clamp_runtime_p0, CLAMP_P0_FORBIDDEN))
    errors.extend(_check_required("AGENTS", agents, AGENTS_REQUIRED))
    return errors


def validate_repository(root: Path) -> list[str]:
    paths = {
        "active": root / "docs" / "ACTIVE_CURRENT.md",
        "architecture": root / "docs" / "ARCHITECTURE.md",
        "cold_start": root / "docs" / "REPOSITORY_COLD_START.md",
        "roadmap": root / "ROADMAP.md",
        "third_party": root / "docs" / "THIRD_PARTY_MODELS.md",
        "clamp_architecture": root / "docs" / "CLAMP3_ARCHITECTURE.md",
        "retrieval_acceptance": root / "docs" / "CLAMP3_RETRIEVAL_ACCEPTANCE.md",
        "clamp_runtime": root / "docs" / "CLAMP3_RUNTIME.md",
        "clamp_runtime_p0": root / "docs" / "CLAMP3_RUNTIME_P0.md",
        "agents": root / "AGENTS.md",
        "pyproject": root / "pyproject.toml",
    }

    missing = [str(path.relative_to(root)) for path in paths.values() if not path.is_file()]
    if missing:
        return [f"missing repository context file: {path}" for path in missing]

    try:
        expected_version = read_project_version(root)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        return [f"project version metadata is invalid: {exc}"]

    return validate_texts(
        active=paths["active"].read_text(encoding="utf-8"),
        architecture=paths["architecture"].read_text(encoding="utf-8"),
        cold_start=paths["cold_start"].read_text(encoding="utf-8"),
        roadmap=paths["roadmap"].read_text(encoding="utf-8"),
        third_party=paths["third_party"].read_text(encoding="utf-8"),
        clamp_architecture=paths["clamp_architecture"].read_text(encoding="utf-8"),
        retrieval_acceptance=paths["retrieval_acceptance"].read_text(encoding="utf-8"),
        clamp_runtime=paths["clamp_runtime"].read_text(encoding="utf-8"),
        clamp_runtime_p0=paths["clamp_runtime_p0"].read_text(encoding="utf-8"),
        agents=paths["agents"].read_text(encoding="utf-8"),
        expected_version=expected_version,
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        print("repository context consistency: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("repository context consistency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
