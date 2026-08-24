from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContextualRecommendation:
    title: str
    recommendation: str
    why_now: str
    competitive_context: str
    training_context: str
    preserve: str | None = None
    secondary_actions: tuple[str, ...] = field(default_factory=tuple)

    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_difficulty: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
    predicts_rank_up: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "recommendation": self.recommendation,
            "why_now": self.why_now,
            "competitive_context": self.competitive_context,
            "training_context": self.training_context,
            "preserve": self.preserve,
            "secondary_actions": list(self.secondary_actions),
            "protections": {
                "changes_learning_priority": self.changes_learning_priority,
                "changes_mission": self.changes_mission,
                "changes_difficulty": self.changes_difficulty,
                "changes_evidence_class": self.changes_evidence_class,
                "counts_as_mission_evidence": self.counts_as_mission_evidence,
                "predicts_rank_up": self.predicts_rank_up,
            },
        }
