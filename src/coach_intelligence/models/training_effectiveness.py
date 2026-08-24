from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskEffectiveness:
    skill_id: str
    task_id: str
    task_title: str
    evaluated_cycles: int
    conclusive_cycles: int
    positive_cycles: int
    stable_cycles: int
    negative_cycles: int
    inconclusive_cycles: int
    effectiveness: str
    confidence: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "evaluated_cycles": self.evaluated_cycles,
            "conclusive_cycles": self.conclusive_cycles,
            "positive_cycles": self.positive_cycles,
            "stable_cycles": self.stable_cycles,
            "negative_cycles": self.negative_cycles,
            "inconclusive_cycles": self.inconclusive_cycles,
            "effectiveness": self.effectiveness,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }
