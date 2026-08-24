from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CrossSkillInsight:
    relationship_id: str
    source_skill_id: str
    target_skill_id: str
    status: str
    confidence: str
    rationale: str
    limitation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_skill_id": self.source_skill_id,
            "target_skill_id": self.target_skill_id,
            "status": self.status,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "limitation": self.limitation,
        }
