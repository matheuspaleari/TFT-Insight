from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TrainingMetricEvaluation:
    metric_id: str
    before: float
    after: float
    delta: float
    relative_change: float | None
    direction: str
    significance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
            "relative_change": self.relative_change,
            "direction": self.direction,
            "significance": self.significance,
        }


@dataclass(frozen=True, slots=True)
class TrainingCycleEvaluation:
    result: str
    confidence: str
    confidence_score: float
    metrics_total: int
    metrics_resolved: int
    positive_metrics: int
    stable_metrics: int
    negative_metrics: int
    before_coverage: float
    after_coverage: float
    before_sample_size: int
    after_sample_size: int
    metric_evaluations: tuple[TrainingMetricEvaluation, ...]
    reason: str
    caveat: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "metrics_total": self.metrics_total,
            "metrics_resolved": self.metrics_resolved,
            "positive_metrics": self.positive_metrics,
            "stable_metrics": self.stable_metrics,
            "negative_metrics": self.negative_metrics,
            "before_coverage": self.before_coverage,
            "after_coverage": self.after_coverage,
            "before_sample_size": self.before_sample_size,
            "after_sample_size": self.after_sample_size,
            "metric_evaluations": [
                item.to_dict()
                for item in self.metric_evaluations
            ],
            "reason": self.reason,
            "caveat": self.caveat,
        }
