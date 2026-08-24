"""
Orquestrador principal do Inspector.
"""

from src.inspector.models import SkillInspection
from src.inspector.services import InspectionService
from src.learning.models import SkillAssessment
from src.performance_engine.models import Performance


class InspectorEngine:
    """
    Explica os resultados produzidos pelo Performance Engine
    e pelo Skill Mapping Service.
    """

    @staticmethod
    def inspect_skill(
        *,
        assessment: SkillAssessment,
        performance: Performance,
    ) -> SkillInspection:
        return InspectionService.inspect_skill(
            assessment=assessment,
            performance=performance,
        )

    @staticmethod
    def inspect_all(
        *,
        assessments: tuple[
            SkillAssessment,
            ...,
        ],
        performance: Performance,
    ) -> tuple[SkillInspection, ...]:
        return InspectionService.inspect_all(
            assessments=assessments,
            performance=performance,
        )