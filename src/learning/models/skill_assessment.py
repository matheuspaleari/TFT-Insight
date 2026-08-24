from dataclasses import dataclass, field

from .skill import Skill
from .skill_level import SkillLevel


@dataclass(slots=True, frozen=True)
class SkillAssessment:
    """
    Representa a avaliação estimada de uma Skill.

    O score é derivado das métricas disponíveis.
    Ele não afirma domínio completo da competência.
    """

    skill: Skill
    score: float
    level: SkillLevel

    confidence: float

    evidence_metric_ids: tuple[str, ...] = field(
        default_factory=tuple
    )

    limitations: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "SkillAssessment.score deve estar entre 0 e 100."
            )

        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(
                "SkillAssessment.confidence deve estar "
                "entre 0 e 100."
            )

    @property
    def stars(self) -> str:
        """
        Representação visual temporária do nível.
        """

        filled = "★" * int(self.level)
        empty = "☆" * (5 - int(self.level))

        return filled + empty