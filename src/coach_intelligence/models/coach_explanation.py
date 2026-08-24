from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CoachExplanation:
    title: str
    summary: str
    next_step: str
    evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    source: str = "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "next_step": self.next_step,
            "evidence": list(self.evidence),
            "limitations": list(self.limitations),
            "source": self.source,
        }
