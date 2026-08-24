from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TASK_DIFFICULTY_ORDER = {
    "FOUNDATION": 0,
    "INTERMEDIATE": 1,
    "ADVANCED": 2,
}


@dataclass(frozen=True, slots=True)
class TaskProgressionDecision:
    skill_id: str
    progression_signal: str
    current_task_id: str
    current_difficulty: str
    selected_task_id: str
    selected_difficulty: str
    changed_task: bool
    changed_difficulty: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "progression_signal": self.progression_signal,
            "current_task_id": self.current_task_id,
            "current_difficulty": self.current_difficulty,
            "selected_task_id": self.selected_task_id,
            "selected_difficulty": self.selected_difficulty,
            "changed_task": self.changed_task,
            "changed_difficulty": self.changed_difficulty,
            "rationale": self.rationale,
        }
