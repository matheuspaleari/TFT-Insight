from dataclasses import dataclass, field

from .explanation_impact import ExplanationImpact


@dataclass(slots=True, frozen=True)
class MatchExplanationFactor:
    factor_id: str
    title: str
    impact: ExplanationImpact

    score: float
    historical_reference: float | None = None
    difference_from_history: float | None = None

    explanation: str = ""
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.factor_id.strip():
            raise ValueError(
                "factor_id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "title não pode ser vazio."
            )

        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "score deve estar entre 0 e 100."
            )
