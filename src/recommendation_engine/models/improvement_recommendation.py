from dataclasses import dataclass, field

from .recommendation_category import (
    RecommendationCategory,
)
from .recommendation_priority import (
    RecommendationPriority,
)


@dataclass(slots=True, frozen=True)
class ImprovementRecommendation:
    recommendation_id: str
    category: RecommendationCategory
    priority: RecommendationPriority

    title: str
    action: str

    current_score: float
    impact_score: float
    confidence: float

    expected_placement_gain: float | None = None

    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.recommendation_id.strip():
            raise ValueError(
                "recommendation_id não pode ser vazio."
            )

        for field_name, value in (
            ("current_score", self.current_score),
            ("impact_score", self.impact_score),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )
