from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgressInsight:
    role: str
    title: str
    message: str
    skill_id: str | None
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "title": self.title,
            "message": self.message,
            "skill_id": self.skill_id,
            "evidence": self.evidence,
        }
