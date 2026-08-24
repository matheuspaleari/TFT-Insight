from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PostMatchReportSection:
    section_id: str
    title: str
    text: str
    importance: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "text": self.text,
            "importance": self.importance,
        }


@dataclass(frozen=True)
class PostMatchReport:
    match_id: str
    player_context: str
    headline: str
    summary: str

    focus_section: PostMatchReportSection
    supporting_sections: tuple[PostMatchReportSection, ...] = field(
        default_factory=tuple
    )

    what_we_cannot_measure: str = ""
    coach_takeaway: str = ""

    source_verdict: str = ""
    baseline_matches: int = 0
    historical_matches: int = 0

    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
    predicts_rank_up: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "player_context": self.player_context,
            "headline": self.headline,
            "summary": self.summary,
            "focus_section": self.focus_section.to_dict(),
            "supporting_sections": [
                item.to_dict()
                for item in self.supporting_sections
            ],
            "what_we_cannot_measure": self.what_we_cannot_measure,
            "coach_takeaway": self.coach_takeaway,
            "source_verdict": self.source_verdict,
            "baseline_matches": self.baseline_matches,
            "historical_matches": self.historical_matches,
            "protections": {
                "changes_learning_priority": self.changes_learning_priority,
                "changes_mission": self.changes_mission,
                "changes_evidence_class": self.changes_evidence_class,
                "counts_as_mission_evidence": self.counts_as_mission_evidence,
                "predicts_rank_up": self.predicts_rank_up,
            },
        }
