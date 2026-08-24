from dataclasses import dataclass, field

from .explanation_factor import ExplanationFactor


@dataclass(slots=True, frozen=True)
class DecisionExplanationReport:
    overall_score: float
    label: str
    headline: str
    summary: str

    positive_factors: tuple[ExplanationFactor, ...] = field(
        default_factory=tuple
    )
    negative_factors: tuple[ExplanationFactor, ...] = field(
        default_factory=tuple
    )
    neutral_factors: tuple[ExplanationFactor, ...] = field(
        default_factory=tuple
    )
    unavailable_factors: tuple[ExplanationFactor, ...] = field(
        default_factory=tuple
    )

    strengths: tuple[str, ...] = field(
        default_factory=tuple
    )
    priorities: tuple[str, ...] = field(
        default_factory=tuple
    )
    caveats: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError(
                "overall_score deve estar entre 0 e 100."
            )

        if not self.label.strip():
            raise ValueError(
                "label não pode ser vazio."
            )

        if not self.headline.strip():
            raise ValueError(
                "headline não pode ser vazio."
            )

        if not self.summary.strip():
            raise ValueError(
                "summary não pode ser vazio."
            )

    @property
    def all_factors(self) -> tuple[ExplanationFactor, ...]:
        return (
            *self.positive_factors,
            *self.negative_factors,
            *self.neutral_factors,
            *self.unavailable_factors,
        )
