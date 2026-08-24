"""
Modelo de saída principal do Coach Engine.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from src.inspector.models import SkillInspection
from src.learning.models import (
    LearningRecommendation,
    SkillAssessment,
)
from src.performance_engine.models import PlayerAnalysisResult
from src.training.models import TrainingMission


@dataclass(slots=True, frozen=True)
class CoachReport:
    """
    Representa o resultado completo entregue pelas interfaces.
    """

    analysis: PlayerAnalysisResult

    skill_assessments: tuple[
        SkillAssessment,
        ...
    ]

    skill_inspections: tuple[
        SkillInspection,
        ...
    ]

    learning_recommendation: LearningRecommendation

    mission: TrainingMission

    coach_message: str

    generated_at: str = ""

    def __post_init__(self) -> None:

        if not self.skill_assessments:
            raise ValueError(
                "CoachReport.skill_assessments não pode ser vazio."
            )

        if not self.skill_inspections:
            raise ValueError(
                "CoachReport.skill_inspections não pode ser vazio."
            )

        if not self.coach_message.strip():
            raise ValueError(
                "CoachReport.coach_message não pode ser vazia."
            )

        if not self.generated_at:
            object.__setattr__(
                self,
                "generated_at",
                datetime.now(
                    timezone.utc,
                ).isoformat(),
            )

    @property
    def riot_id(self) -> str:
        return self.analysis.riot_id

    @property
    def performance(self):
        return self.analysis.performance

    @property
    def current_skill(self):
        return self.learning_recommendation.skill

    @property
    def current_inspection(
        self,
    ) -> SkillInspection:
        """
        Retorna a inspeção correspondente
        à Skill recomendada.
        """

        current_skill_id = (
            self.learning_recommendation
            .skill
            .id
        )

        for inspection in self.skill_inspections:

            if (
                inspection.skill_id
                == current_skill_id
            ):
                return inspection

        raise RuntimeError(
            "A inspeção da Skill recomendada "
            "não foi encontrada."
        )