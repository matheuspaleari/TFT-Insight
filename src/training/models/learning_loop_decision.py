from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LearningLoopDecision:
    priority_skill_id: str
    post_cycle_action: str
    anti_loop_action: str
    progression_signal: str
    selected_task_id: str | None
    selected_difficulty: str | None
    previous_task_id: str | None
    previous_result: str | None
    trend: str
    trend_confidence: str
    consecutive_skill_cycles: int
    defer_new_mission: bool
    requires_priority_reassessment: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority_skill_id": self.priority_skill_id,
            "post_cycle_action": self.post_cycle_action,
            "anti_loop_action": self.anti_loop_action,
            "progression_signal": self.progression_signal,
            "selected_task_id": self.selected_task_id,
            "selected_difficulty": self.selected_difficulty,
            "previous_task_id": self.previous_task_id,
            "previous_result": self.previous_result,
            "trend": self.trend,
            "trend_confidence": self.trend_confidence,
            "consecutive_skill_cycles": self.consecutive_skill_cycles,
            "defer_new_mission": self.defer_new_mission,
            "requires_priority_reassessment": (
                self.requires_priority_reassessment
            ),
            "rationale": self.rationale,
        }
