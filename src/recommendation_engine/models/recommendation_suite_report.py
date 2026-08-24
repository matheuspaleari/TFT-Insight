from dataclasses import dataclass, field

from .composition_recommendation import (
    CompositionRecommendation,
)
from .contest_recommendation import (
    ContestRecommendation,
)
from .economy_recommendation import (
    EconomyRecommendation,
)
from .improvement_priority_report import (
    ImprovementPriorityReport,
)
from .playstyle_profile import PlaystyleProfile


@dataclass(slots=True, frozen=True)
class RecommendationSuiteReport:
    priorities: ImprovementPriorityReport
    playstyle: PlaystyleProfile
    contest: ContestRecommendation
    economy: EconomyRecommendation

    compositions: tuple[
        CompositionRecommendation,
        ...,
    ] = field(default_factory=tuple)

    summary: str = ""
