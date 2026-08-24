from dataclasses import dataclass

from .analysis_availability import (
    AnalysisAvailability,
)


@dataclass(slots=True, frozen=True)
class EconomyReport:
    availability: AnalysisAvailability

    score: float
    label: str

    average_level: float
    average_gold_left: float
    average_last_round: float

    level_8_rate: float
    level_9_rate: float
    low_level_late_rate: float

    matches_analyzed: int
    summary: str
