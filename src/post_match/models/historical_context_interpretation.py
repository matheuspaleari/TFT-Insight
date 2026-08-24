from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HistoricalInterpretationItem:
    metric_id: str
    title: str
    text: str
    importance: int
    internal_signal: str
    direction_is_quality: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "title": self.title,
            "text": self.text,
            "importance": self.importance,
            "internal_signal": self.internal_signal,
            "direction_is_quality": self.direction_is_quality,
        }


@dataclass(frozen=True)
class HistoricalContextInterpretation:
    overview: str
    focus_reading: str
    additional_readings: tuple[HistoricalInterpretationItem, ...] = field(default_factory=tuple)
    conclusion: str = ""
    changes_evidence_class: bool = False
    changes_learning_priority: bool = False
    changes_mission: bool = False
    counts_as_mission_evidence: bool = False
