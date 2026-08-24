from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class PlaystyleProfile:
    primary_style: str
    confidence: float

    fast_8_score: float
    fast_9_score: float
    reroll_score: float
    flexible_score: float
    aggressive_score: float

    explanation: str
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )
