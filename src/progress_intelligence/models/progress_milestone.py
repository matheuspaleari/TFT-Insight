from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgressMilestone:
    milestone_id: str
    skill_id: str
    milestone_type: str
    title: str
    description: str
    detected_at: str
    from_value: Any = None
    to_value: Any = None
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "skill_id": self.skill_id,
            "milestone_type": self.milestone_type,
            "title": self.title,
            "description": self.description,
            "detected_at": self.detected_at,
            "from_value": self.from_value,
            "to_value": self.to_value,
            "evidence": self.evidence or {},
        }
