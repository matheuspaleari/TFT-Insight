from dataclasses import dataclass, field

from .prediction_risk import PredictionRisk


@dataclass(slots=True, frozen=True)
class MatchPredictionReport:
    top4_probability: float
    win_probability: float
    expected_placement: float

    risk: PredictionRisk
    confidence: float

    positive_signals: tuple[str, ...] = field(
        default_factory=tuple
    )
    risk_signals: tuple[str, ...] = field(
        default_factory=tuple
    )
    caveats: tuple[str, ...] = field(
        default_factory=tuple
    )

    summary: str = ""

    def __post_init__(self) -> None:
        for field_name, value in (
            ("top4_probability", self.top4_probability),
            ("win_probability", self.win_probability),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )

        if not 1.0 <= self.expected_placement <= 8.0:
            raise ValueError(
                "expected_placement deve estar entre 1 e 8."
            )
