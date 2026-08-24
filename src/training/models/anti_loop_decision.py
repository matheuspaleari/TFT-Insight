from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AntiLoopDecision:
    skill_id: str
    action: str
    task_progression: str
    trend: str
    trend_confidence: str
    consecutive_skill_cycles: int
    evaluated_cycles: int
    conclusive_cycles: int
    recent_results: tuple[str, ...]
    rationale: str
    caution: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "action": self.action,
            "task_progression": self.task_progression,
            "trend": self.trend,
            "trend_confidence": self.trend_confidence,
            "consecutive_skill_cycles": self.consecutive_skill_cycles,
            "evaluated_cycles": self.evaluated_cycles,
            "conclusive_cycles": self.conclusive_cycles,
            "recent_results": list(self.recent_results),
            "rationale": self.rationale,
            "caution": self.caution,
        }
