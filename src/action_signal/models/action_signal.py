from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionSignalStrength(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    WATCH = "WATCH"


class ActionSignalEvidence(str, Enum):
    OBSERVED = "OBSERVED"
    HISTORICAL = "HISTORICAL"
    COMBINED = "COMBINED"


@dataclass(frozen=True)
class ActionSignal:
    signal_id: str
    title: str
    action: str
    reason: str
    strength: ActionSignalStrength
    evidence: ActionSignalEvidence
    skill_id: str | None = None
    metric_id: str | None = None
    confidence: float = 0.5
    safe_for_player: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "title": self.title,
            "action": self.action,
            "reason": self.reason,
            "strength": self.strength.value,
            "evidence": self.evidence.value,
            "skill_id": self.skill_id,
            "metric_id": self.metric_id,
            "confidence": self.confidence,
            "safe_for_player": self.safe_for_player,
        }


@dataclass(frozen=True)
class ActionSignalReport:
    primary: ActionSignal | None
    secondary: tuple[ActionSignal, ...] = field(default_factory=tuple)
    watch: tuple[ActionSignal, ...] = field(default_factory=tuple)
    summary: str = ""

    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_difficulty: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
    predicts_rank_up: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary.to_dict() if self.primary else None,
            "secondary": [item.to_dict() for item in self.secondary],
            "watch": [item.to_dict() for item in self.watch],
            "summary": self.summary,
            "protections": {
                "changes_learning_priority": self.changes_learning_priority,
                "changes_mission": self.changes_mission,
                "changes_difficulty": self.changes_difficulty,
                "changes_evidence_class": self.changes_evidence_class,
                "counts_as_mission_evidence": self.counts_as_mission_evidence,
                "predicts_rank_up": self.predicts_rank_up,
            },
        }
