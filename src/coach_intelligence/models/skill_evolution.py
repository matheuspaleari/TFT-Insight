from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillEvolution:
    skill_id: str
    previous_score: float | None
    current_score: float | None
    score_delta: float | None
    previous_level: str | None
    current_level: str
    training_trend: str
    direction: str
    confidence: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "previous_score": self.previous_score,
            "current_score": self.current_score,
            "score_delta": self.score_delta,
            "previous_level": self.previous_level,
            "current_level": self.current_level,
            "training_trend": self.training_trend,
            "direction": self.direction,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }
