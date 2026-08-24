from dataclasses import dataclass, field

from .explanation_impact import ExplanationImpact


@dataclass(slots=True, frozen=True)
class ExplanationFactor:
    factor_id: str
    title: str
    impact: ExplanationImpact

    score: float | None = None
    weight: float = 0.0
    contribution: float = 0.0

    explanation: str = ""
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.factor_id.strip():
            raise ValueError(
                "ExplanationFactor.factor_id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "ExplanationFactor.title não pode ser vazio."
            )

        if self.score is not None and not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "ExplanationFactor.score deve estar entre 0 e 100."
            )

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                "ExplanationFactor.weight deve estar entre 0 e 1."
            )
