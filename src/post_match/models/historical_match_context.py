from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class HistoricalSignal(str, Enum):
    IMPROVING = "IMPROVING"
    WORSENING = "WORSENING"
    RECURRING_LOW = "RECURRING_LOW"
    RECURRING_HIGH = "RECURRING_HIGH"
    STABLE = "STABLE"
    ATYPICAL_LOW = "ATYPICAL_LOW"
    ATYPICAL_HIGH = "ATYPICAL_HIGH"
    INSUFFICIENT = "INSUFFICIENT"

@dataclass(frozen=True)
class HistoricalMetricContext:
    metric_id: str
    label: str
    signal: HistoricalSignal
    recent_mean: float | None
    previous_mean: float | None
    recent_matches: int
    previous_matches: int
    repeated_count: int
    current_band: str | None
    explanation: str

@dataclass(frozen=True)
class HistoricalMatchContext:
    target_match_id: str
    metrics: tuple[HistoricalMetricContext, ...] = field(default_factory=tuple)
    summary: str = ""
    changes_evidence_class: bool = False
    changes_learning_priority: bool = False
    changes_mission: bool = False
    counts_as_mission_evidence: bool = False
