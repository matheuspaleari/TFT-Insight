from dataclasses import dataclass
from typing import Any

from .skill import Skill
from .skill_assessment import SkillAssessment


@dataclass(slots=True, frozen=True)
class LearningRecommendation:
    """
    Representa a decisão pedagógica do Learning Engine.

    Responde à pergunta:

        "O que devemos ensinar agora?"
    """

    skill: Skill
    assessment: SkillAssessment

    reason: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "LearningRecommendation.reason não pode ser vazio."
            )

        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(
                "LearningRecommendation.confidence deve estar "
                "entre 0 e 100."
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte a recomendação em um dicionário serializável.
        """

        return {
            "skill": {
                "id": self.skill.id,
                "title": self.skill.title,
                "description": self.skill.description,
                "prerequisite_ids": list(
                    self.skill.prerequisite_ids
                ),
                "related_metric_ids": list(
                    self.skill.related_metric_ids
                ),
            },
            "assessment": {
                "score": self.assessment.score,
                "level": int(self.assessment.level),
                "confidence": self.assessment.confidence,
                "evidence_metric_ids": list(
                    self.assessment.evidence_metric_ids
                ),
                "limitations": list(
                    self.assessment.limitations
                ),
            },
            "reason": self.reason,
            "confidence": self.confidence,
        }