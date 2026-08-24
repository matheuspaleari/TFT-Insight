from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ContestRecommendation:
    action: str
    confidence: float

    carry_contest_rate: float
    high_contest_rate: float
    placement_impact: float | None

    explanation: str
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )
