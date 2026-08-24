from dataclasses import dataclass, field

from .match_explanation_factor import (
    MatchExplanationFactor,
)


@dataclass(slots=True, frozen=True)
class MatchDecisionExplanationReport:
    match_id: str
    placement: int

    overall_score: float
    label: str
    headline: str
    summary: str

    strongest_factor: MatchExplanationFactor | None
    weakest_factor: MatchExplanationFactor | None

    positive_factors: tuple[
        MatchExplanationFactor,
        ...,
    ] = field(default_factory=tuple)

    attention_factors: tuple[
        MatchExplanationFactor,
        ...,
    ] = field(default_factory=tuple)

    critical_factors: tuple[
        MatchExplanationFactor,
        ...,
    ] = field(default_factory=tuple)

    neutral_factors: tuple[
        MatchExplanationFactor,
        ...,
    ] = field(default_factory=tuple)

    recommendations: tuple[str, ...] = field(
        default_factory=tuple
    )

    caveats: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.match_id.strip():
            raise ValueError(
                "match_id não pode ser vazio."
            )

        if not 1 <= self.placement <= 8:
            raise ValueError(
                "placement deve estar entre 1 e 8."
            )

        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError(
                "overall_score deve estar entre 0 e 100."
            )

    @property
    def all_factors(
        self,
    ) -> tuple[MatchExplanationFactor, ...]:
        return (
            *self.positive_factors,
            *self.attention_factors,
            *self.critical_factors,
            *self.neutral_factors,
        )
