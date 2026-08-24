from __future__ import annotations

from dataclasses import dataclass

from src.learning.models.skill_level import (
    SkillLevel,
)


@dataclass(frozen=True)
class SkillSignal:
    """
    Evidência de Skill derivada de Habits.

    Um SkillSignal NÃO substitui o SkillAssessment atual.
    Ele é a ponte entre padrões históricos e a avaliação de Skills.

    `assessable=False` significa que o histórico traz contexto relacionado
    à Skill, mas não observa diretamente a competência necessária para
    atribuir um nível de domínio com segurança.
    """

    skill_id: str
    skill_label: str
    direction: str
    confidence: float
    assessable: bool
    level_hint: SkillLevel | None
    habit_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    interpretation: str
    limitations: tuple[str, ...] = ()
