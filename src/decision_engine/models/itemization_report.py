from dataclasses import dataclass

from .analysis_availability import (
    AnalysisAvailability,
)


@dataclass(slots=True, frozen=True)
class ItemizationReport:
    availability: AnalysisAvailability

    score: float
    label: str

    carry_item_share: float
    tank_item_share: float
    support_item_share: float
    unknown_item_share: float

    carry_full_item_rate: float
    tank_full_item_rate: float

    matches_analyzed: int
    summary: str
