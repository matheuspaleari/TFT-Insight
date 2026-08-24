from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PostMatchVerdict(str, Enum):
    POSITIVE = "POSITIVE"
    MIXED = "MIXED"
    NEGATIVE = "NEGATIVE"
    OBSERVATIONAL = "OBSERVATIONAL"
    NOT_EVALUATED = "NOT_EVALUATED"


class EvidenceClass(str, Enum):
    DIRECT = "DIRECT"
    PROXY = "PROXY"
    CONTEXT = "CONTEXT"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(slots=True, frozen=True)
class PostMatchEvidence:
    signal_id: str
    label: str
    value: str
    interpretation: str
    evidence_class: EvidenceClass
    relation: str = "context"
    confidence: float | None = None
    source: str = "match"
    supports_mission_evaluation: bool = False
    limitation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "label": self.label,
            "value": self.value,
            "interpretation": self.interpretation,
            "evidence_class": self.evidence_class.value,
            "relation": self.relation,
            "confidence": self.confidence,
            "source": self.source,
            "supports_mission_evaluation": self.supports_mission_evaluation,
            "limitation": self.limitation,
        }


@dataclass(slots=True, frozen=True)
class PostMatchAnalysis:
    match_id: str
    placement: int
    level: int
    gold_left: int
    last_round: int
    players_eliminated: int
    total_damage_to_players: int
    active_skill_id: str | None = None
    active_skill_label: str | None = None
    mission_title: str | None = None
    mission_objective: str | None = None
    verdict: PostMatchVerdict = PostMatchVerdict.OBSERVATIONAL
    verdict_reason: str = ""
    headline: str = ""
    summary: str = ""
    evidence: tuple[PostMatchEvidence, ...] = field(default_factory=tuple)
    unavailable_evidence: tuple[PostMatchEvidence, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    direct_count: int = 0
    proxy_count: int = 0
    context_count: int = 0
    unavailable_count: int = 0
    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_difficulty: bool = False
    predicts_rank_up: bool = False
    counts_as_mission_evidence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "placement": self.placement,
            "level": self.level,
            "gold_left": self.gold_left,
            "last_round": self.last_round,
            "players_eliminated": self.players_eliminated,
            "total_damage_to_players": self.total_damage_to_players,
            "active_skill_id": self.active_skill_id,
            "active_skill_label": self.active_skill_label,
            "mission_title": self.mission_title,
            "mission_objective": self.mission_objective,
            "verdict": self.verdict.value,
            "verdict_reason": self.verdict_reason,
            "headline": self.headline,
            "summary": self.summary,
            "evidence": [item.to_dict() for item in self.evidence],
            "unavailable_evidence": [item.to_dict() for item in self.unavailable_evidence],
            "evidence_summary": {
                "direct": self.direct_count,
                "proxy": self.proxy_count,
                "context": self.context_count,
                "unavailable": self.unavailable_count,
            },
            "limitations": list(self.limitations),
            "protections": {
                "changes_learning_priority": self.changes_learning_priority,
                "changes_mission": self.changes_mission,
                "changes_difficulty": self.changes_difficulty,
                "predicts_rank_up": self.predicts_rank_up,
                "counts_as_mission_evidence": self.counts_as_mission_evidence,
            },
        }
