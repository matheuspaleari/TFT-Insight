from dataclasses import dataclass, field

from .improvement_recommendation import (
    ImprovementRecommendation,
)


@dataclass(slots=True, frozen=True)
class ImprovementPriorityReport:
    recommendations: tuple[
        ImprovementRecommendation,
        ...,
    ] = field(default_factory=tuple)

    strongest_area: str = ""
    summary: str = ""

    @property
    def primary_priority(
        self,
    ) -> ImprovementRecommendation | None:
        return (
            self.recommendations[0]
            if self.recommendations
            else None
        )
