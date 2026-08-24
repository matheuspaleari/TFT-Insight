from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class CompositionRecommendation:
    composition_key: str
    carry_character_id: str

    matches_played: int
    average_placement: float
    top4_rate: float
    win_rate: float
    average_contest_score: float | None

    recommendation_score: float
    label: str
    explanation: str

    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )
