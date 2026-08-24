"""
Modelo que representa a inspeção de uma Skill.
"""

from dataclasses import dataclass, field

from src.learning.models import SkillAssessment

from .metric_inspection import MetricInspection


@dataclass(slots=True, frozen=True)
class SkillInspection:
    """
    Reúne o diagnóstico completo de uma competência.

    O Inspector não cria uma nova avaliação. Ele explica
    a avaliação que já foi produzida pelo Learning Engine.
    """

    assessment: SkillAssessment

    metric_inspections: tuple[
        MetricInspection,
        ...,
    ] = field(
        default_factory=tuple,
    )

    summary: str = ""

    @property
    def skill_id(self) -> str:
        return self.assessment.skill.id

    @property
    def skill_title(self) -> str:
        return self.assessment.skill.title

    @property
    def score(self) -> float:
        return self.assessment.score

    @property
    def confidence(self) -> float:
        return self.assessment.confidence

    @property
    def has_evidence(self) -> bool:
        return bool(
            self.metric_inspections
        )

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.assessment.limitations