from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class ProgressCoachingStrategy:
    priority_skill_id: str
    action: str
    confidence: str
    progress_signal: str
    current_task_id: str | None
    current_difficulty: str | None
    rationale: str
    safeguards: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority_skill_id": self.priority_skill_id,
            "action": self.action,
            "confidence": self.confidence,
            "progress_signal": self.progress_signal,
            "current_task_id": self.current_task_id,
            "current_difficulty": self.current_difficulty,
            "rationale": self.rationale,
            "safeguards": list(self.safeguards),
        }
