from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningPriority:
    """
    Prioridade de treino produzida pelo Learning Priority Engine.

    `internal_score` serve apenas para ordenação interna e não deve ser
    apresentado ao jogador como métrica de TFT.
    """

    skill_id: str
    skill_label: str
    role: str
    rank: int
    internal_score: float
    confidence: float
    training_focus: str
    reason: str
    evidence_status: str
    source_decision: str
    habit_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class LearningPriorityPlan:
    primary: LearningPriority | None
    secondary: tuple[LearningPriority, ...]
    strengths: tuple[LearningPriority, ...]
    context: tuple[LearningPriority, ...]
