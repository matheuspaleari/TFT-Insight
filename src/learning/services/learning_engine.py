"""
Motor responsável por decidir qual Skill deve ser ensinada.
"""

from src.learning.models import (
    LearningRecommendation,
    SkillAssessment,
    SkillLevel,
)


class LearningEngine:
    """
    Decide qual Skill será treinada na sessão atual.
    """

    @classmethod
    def recommend(
        cls,
        assessments: tuple[SkillAssessment, ...],
    ) -> LearningRecommendation:

        evaluated = [
            assessment
            for assessment in assessments
            if assessment.level
            != SkillLevel.NOT_EVALUATED
        ]

        if not evaluated:
            raise RuntimeError(
                "Nenhuma Skill pôde ser avaliada."
            )

        evaluated.sort(
            key=lambda item: (
                item.score,
                -item.confidence,
            )
        )

        selected = evaluated[0]

        return LearningRecommendation(
            skill=selected.skill,
            assessment=selected,
            confidence=selected.confidence,
            reason=(
                "Menor nível de domínio entre as "
                "competências avaliadas."
            ),
        )