from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillTrainingCycleSummary:
    cycle_id: str
    skill_id: str
    task_id: str | None
    task_title: str | None
    result: str | None
    confidence: str | None
    confidence_score: float | None
    evaluated_at: str | None
    is_conclusive: bool
    signal: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "skill_id": self.skill_id,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "result": self.result,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "evaluated_at": self.evaluated_at,
            "is_conclusive": self.is_conclusive,
            "signal": self.signal,
        }


@dataclass(frozen=True, slots=True)
class SkillTrainingHistory:
    skill_id: str
    cycles_total: int
    evaluated_cycles: int
    conclusive_cycles: int
    positive_cycles: int
    stable_cycles: int
    negative_cycles: int
    inconclusive_cycles: int
    trend: str
    trend_confidence: str
    latest_result: str | None
    previous_result: str | None
    cycles: tuple[SkillTrainingCycleSummary, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "cycles_total": self.cycles_total,
            "evaluated_cycles": self.evaluated_cycles,
            "conclusive_cycles": self.conclusive_cycles,
            "positive_cycles": self.positive_cycles,
            "stable_cycles": self.stable_cycles,
            "negative_cycles": self.negative_cycles,
            "inconclusive_cycles": self.inconclusive_cycles,
            "trend": self.trend,
            "trend_confidence": self.trend_confidence,
            "latest_result": self.latest_result,
            "previous_result": self.previous_result,
            "cycles": [
                cycle.to_dict()
                for cycle in self.cycles
            ],
            "rationale": self.rationale,
        }
