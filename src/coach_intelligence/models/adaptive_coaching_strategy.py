from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AdaptiveCoachingStrategy:
    priority_skill_id: str
    strategy: str
    confidence: str
    current_level: str
    current_score: float | None
    training_trend: str
    current_difficulty: str | None
    current_task_id: str | None
    task_effectiveness: str
    anti_loop_action: str
    rationale: str
    safeguards: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority_skill_id": self.priority_skill_id,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "current_level": self.current_level,
            "current_score": self.current_score,
            "training_trend": self.training_trend,
            "current_difficulty": self.current_difficulty,
            "current_task_id": self.current_task_id,
            "task_effectiveness": self.task_effectiveness,
            "anti_loop_action": self.anti_loop_action,
            "rationale": self.rationale,
            "safeguards": list(self.safeguards),
        }
