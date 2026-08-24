from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SkillProgressPoint:
    snapshot_id: str
    created_at: str
    skill_id: str
    score: float | None
    level: str
    trend: str
    trend_confidence: str
    cycles_total: int
    conclusive_cycles: int
    difficulty: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "skill_id": self.skill_id,
            "score": self.score,
            "level": self.level,
            "trend": self.trend,
            "trend_confidence": self.trend_confidence,
            "cycles_total": self.cycles_total,
            "conclusive_cycles": self.conclusive_cycles,
            "difficulty": self.difficulty,
        }
