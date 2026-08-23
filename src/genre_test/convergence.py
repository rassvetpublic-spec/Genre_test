from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

from .comparison import SEVERITY_ORDER, ComparisonResult, compare_results
from .models import AnalysisResult


@dataclass(frozen=True)
class ModeConvergence:
    level: str
    worst_severity: str
    comparisons: dict[str, ComparisonResult]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["comparisons"] = {key: value.to_dict() for key, value in self.comparisons.items()}
        return data


def compare_modes(results: dict[str, AnalysisResult]) -> ModeConvergence:
    pairwise: dict[str, ComparisonResult] = {}
    worst = "STABLE"
    for left_mode, right_mode in combinations(sorted(results), 2):
        comparison = compare_results(results[left_mode], results[right_mode])
        pairwise[f"{left_mode}_vs_{right_mode}"] = comparison
        if SEVERITY_ORDER[comparison.severity] > SEVERITY_ORDER[worst]:
            worst = comparison.severity

    level = {
        "STABLE": "HIGH",
        "MINOR": "MEDIUM",
        "SIGNIFICANT": "LOW",
        "CRITICAL": "FAIL",
    }[worst]
    return ModeConvergence(level=level, worst_severity=worst, comparisons=pairwise)
