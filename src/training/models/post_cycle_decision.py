from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PostCycleDecision:
    action: str
    target_skill_id: str
    previous_skill_id: str | None
    previous_task_id: str | None
    previous_result: str | None
    previous_confidence: str | None
    task_strategy: str
    suggested_task_id: str | None
    excluded_task_ids: tuple[str, ...]
    rationale: str
    history_used: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target_skill_id": self.target_skill_id,
            "previous_skill_id": self.previous_skill_id,
            "previous_task_id": self.previous_task_id,
            "previous_result": self.previous_result,
            "previous_confidence": self.previous_confidence,
            "task_strategy": self.task_strategy,
            "suggested_task_id": self.suggested_task_id,
            "excluded_task_ids": list(
                self.excluded_task_ids
            ),
            "rationale": self.rationale,
            "history_used": self.history_used,
        }
