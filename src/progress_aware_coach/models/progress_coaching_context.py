from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class ProgressCoachingContext:
    skill_id: str
    snapshot_count: int
    first_score: float | None
    latest_score: float | None
    delta: float | None
    recent_direction: str
    signal: str
    confidence: str
    consecutive_moves: int
    enough_for_reaction: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "snapshot_count": self.snapshot_count,
            "first_score": self.first_score,
            "latest_score": self.latest_score,
            "delta": self.delta,
            "recent_direction": self.recent_direction,
            "signal": self.signal,
            "confidence": self.confidence,
            "consecutive_moves": self.consecutive_moves,
            "enough_for_reaction": self.enough_for_reaction,
            "reason": self.reason,
        }
