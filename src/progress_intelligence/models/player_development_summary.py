from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlayerDevelopmentSummary:
    status: str
    confidence: str
    primary_skill_id: str | None
    improving_skills: tuple[str, ...] = field(default_factory=tuple)
    stable_skills: tuple[str, ...] = field(default_factory=tuple)
    regressing_skills: tuple[str, ...] = field(default_factory=tuple)
    insufficient_skills: tuple[str, ...] = field(default_factory=tuple)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "primary_skill_id": self.primary_skill_id,
            "improving_skills": list(self.improving_skills),
            "stable_skills": list(self.stable_skills),
            "regressing_skills": list(self.regressing_skills),
            "insufficient_skills": list(self.insufficient_skills),
            "rationale": self.rationale,
        }
