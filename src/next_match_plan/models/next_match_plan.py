from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class NextMatchPlan:
    active_skill_label: str
    mission_title: str
    mission_objective: str
    primary_title: str
    primary_action: str
    watch_items: tuple[str, ...] = field(default_factory=tuple)
    preserve: str | None = None
    coach_reminder: str = ""
    publishable: bool = True
    blocked_reason: str | None = None

    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_difficulty: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
    predicts_rank_up: bool = False
