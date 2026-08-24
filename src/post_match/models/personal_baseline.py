from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PersonalComparisonBand(str, Enum):
    ABOVE = "ABOVE"
    WITHIN = "WITHIN"
    BELOW = "BELOW"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(slots=True, frozen=True)
class PersonalMetricComparison:
    metric_id: str
    label: str
    current_value: float
    baseline_mean: float | None
    baseline_std: float | None
    sample_size: int
    higher_is_better: bool
    band: PersonalComparisonBand
    delta: float | None = None
    z_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "label": self.label,
            "current_value": self.current_value,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "sample_size": self.sample_size,
            "higher_is_better": self.higher_is_better,
            "band": self.band.value,
            "delta": self.delta,
            "z_score": self.z_score,
        }


@dataclass(slots=True, frozen=True)
class PersonalBaselineReport:
    target_match_id: str
    requested_history_size: int
    matches_used: int
    comparisons: tuple[PersonalMetricComparison, ...] = field(
        default_factory=tuple
    )
    summary: str = ""
    changes_evidence_class: bool = False
    changes_learning_priority: bool = False
    counts_as_mission_evidence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_match_id": self.target_match_id,
            "requested_history_size": self.requested_history_size,
            "matches_used": self.matches_used,
            "comparisons": [
                item.to_dict()
                for item in self.comparisons
            ],
            "summary": self.summary,
            "protections": {
                "changes_evidence_class": self.changes_evidence_class,
                "changes_learning_priority": self.changes_learning_priority,
                "counts_as_mission_evidence": self.counts_as_mission_evidence,
            },
        }
