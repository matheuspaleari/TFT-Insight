from dataclasses import dataclass, field

from .confidence import AnalysisConfidence


@dataclass(slots=True, frozen=True)
class SprintPredictionReport:
    top1_probability: float
    top4_probability: float
    bot4_probability: float
    expected_placement: float
    risk: str
    confidence: AnalysisConfidence
    positive_signals: tuple[str, ...] = field(default_factory=tuple)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (
            ("top1_probability", self.top1_probability),
            ("top4_probability", self.top4_probability),
            ("bot4_probability", self.bot4_probability),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} deve estar entre 0 e 100.")
        if not 1.0 <= self.expected_placement <= 8.0:
            raise ValueError("expected_placement deve estar entre 1 e 8.")
