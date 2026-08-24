from dataclasses import dataclass

from .analysis_availability import (
    AnalysisAvailability,
)


@dataclass(slots=True, frozen=True)
class PositioningReport:
    availability: AnalysisAvailability
    summary: str
