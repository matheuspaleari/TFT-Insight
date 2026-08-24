from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class EconomyRecommendation:
    action: str
    confidence: float

    average_level: float
    level_8_rate: float
    level_9_rate: float
    low_level_late_rate: float
    average_gold_left: float

    explanation: str
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )
