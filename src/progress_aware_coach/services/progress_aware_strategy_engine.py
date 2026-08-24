from __future__ import annotations
from src.progress_aware_coach.models.progress_coaching_strategy import ProgressCoachingStrategy

class ProgressAwareStrategyEngine:
    """Fases 13.2-13.4: reage a progresso sem escolher outra Skill."""

    @classmethod
    def decide(cls, *, context, adaptive_strategy: dict | None) -> ProgressCoachingStrategy:
        adaptive_strategy = adaptive_strategy if isinstance(adaptive_strategy, dict) else {}
        task = adaptive_strategy.get("current_task_id")
        difficulty = adaptive_strategy.get("current_difficulty")

        if context.signal == "REGRESSION" and context.enough_for_reaction:
            action = "REINFORCE_FOUNDATION"
            rationale = "A queda deixou de ser um ponto isolado e virou sequência observada. Preserve a Skill e reforce a execução antes de aumentar a exigência."
        elif context.signal == "IMPROVEMENT" and context.enough_for_reaction:
            action = "RECOGNIZE_AND_PREPARE_ADVANCE"
            rationale = "A melhora aparece em sequência. Reconheça o progresso e prepare progressão, sem avançar automaticamente a dificuldade."
        elif context.signal == "WATCH":
            action = "OBSERVE"
            rationale = "Existe mudança observada, mas o histórico ainda é curto. Mantenha a abordagem atual e colete mais evidência."
        else:
            action = "MAINTAIN"
            rationale = "O histórico não apresenta direção consistente suficiente para adaptar a abordagem agora."

        return ProgressCoachingStrategy(
            priority_skill_id=context.skill_id,
            action=action,
            confidence=context.confidence,
            progress_signal=context.signal,
            current_task_id=task,
            current_difficulty=difficulty,
            rationale=rationale,
            safeguards=(
                "Learning Priority continua sendo a única fonte da Skill prioritária.",
                "Dois snapshots não bastam para declarar regressão ou melhora persistente.",
                "Progress Intelligence orienta como treinar; não troca missão automaticamente.",
            ),
        )
