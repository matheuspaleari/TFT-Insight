from dataclasses import dataclass

from .analysis_availability import (
    AnalysisAvailability,
)


@dataclass(slots=True, frozen=True)
class AugmentReport:
    availability: AnalysisAvailability

    augments_detected: int
    unique_augments: int
    summary: str
