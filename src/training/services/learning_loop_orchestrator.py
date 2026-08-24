from __future__ import annotations

from typing import Any

from src.training.knowledge import get_tasks_for_skill
from src.training.models.learning_loop_decision import (
    LearningLoopDecision,
)
from src.training.services.anti_loop_training_guard import (
    AntiLoopTrainingGuard,
)
from src.training.services.post_cycle_decision_engine import (
    PostCycleDecisionEngine,
)
from src.training.services.task_difficulty_progression_engine import (
    TaskDifficultyProgressionEngine,
)


class LearningLoopOrchestrator:
    """
    Integra Post-Cycle + tendência + Anti-Loop + dificuldade.

    Regra de arquitetura:
    - Learning Priority continua escolhendo QUAL Skill treinar.
    - este orchestrator decide COMO treinar a Skill recebida.
    """

    @classmethod
    def decide(
        cls,
        *,
        priority_skill_id: str,
        completed_mission: dict[str, Any] | None,
        training_history: list[dict[str, Any]],
    ) -> LearningLoopDecision:
        post_cycle = PostCycleDecisionEngine.decide(
            priority_skill_id=priority_skill_id,
            completed_mission=completed_mission,
            training_history=training_history,
        )

        guard = AntiLoopTrainingGuard.evaluate(
            skill_id=priority_skill_id,
            training_history=training_history,
        )

        tasks = tuple(
            get_tasks_for_skill(
                priority_skill_id
            )
        )

        if not tasks:
            raise RuntimeError(
                "Nenhuma task cadastrada para a Skill: "
                f"{priority_skill_id}"
            )

        base_task_id = (
            post_cycle.suggested_task_id
            or post_cycle.previous_task_id
            or tasks[0].id
        )

        selected_task_id = base_task_id
        selected_difficulty = cls._difficulty(
            tasks=tasks,
            task_id=base_task_id,
        )

        progression_signal = guard.task_progression

        # HOLD significa que o histórico de longo prazo não precisa
        # sobrescrever a decisão imediata do Post-Cycle.
        if progression_signal != "HOLD":
            current_task_id = (
                post_cycle.previous_task_id
                or base_task_id
            )

            progression = (
                TaskDifficultyProgressionEngine.decide(
                    skill_id=priority_skill_id,
                    current_task_id=current_task_id,
                    progression_signal=progression_signal,
                )
            )

            selected_task_id = (
                progression.selected_task_id
            )
            selected_difficulty = (
                progression.selected_difficulty
            )

        # COOLDOWN é o único estado que não cria outra missão na mesma
        # Skill automaticamente. A prioridade precisa ser reavaliada.
        defer_new_mission = (
            guard.action == "COOLDOWN_SKILL"
        )

        requires_priority_reassessment = (
            guard.action
            in {
                "REASSESS",
                "COOLDOWN_SKILL",
            }
        )

        rationale_parts = [
            post_cycle.rationale,
            guard.rationale,
        ]

        if progression_signal == "HOLD":
            rationale_parts.append(
                "O sinal HOLD preservou a escolha imediata do "
                "Post-Cycle sem aumentar dificuldade."
            )
        elif selected_task_id:
            rationale_parts.append(
                "A progressão formal selecionou "
                f"{selected_task_id} ({selected_difficulty})."
            )

        if defer_new_mission:
            rationale_parts.append(
                "Como o Anti-Loop entrou em COOLDOWN_SKILL, "
                "uma nova missão da mesma Skill foi adiada até "
                "uma nova avaliação de prioridade."
            )

        return LearningLoopDecision(
            priority_skill_id=priority_skill_id,
            post_cycle_action=post_cycle.action,
            anti_loop_action=guard.action,
            progression_signal=progression_signal,
            selected_task_id=selected_task_id,
            selected_difficulty=selected_difficulty,
            previous_task_id=post_cycle.previous_task_id,
            previous_result=post_cycle.previous_result,
            trend=guard.trend,
            trend_confidence=guard.trend_confidence,
            consecutive_skill_cycles=(
                guard.consecutive_skill_cycles
            ),
            defer_new_mission=defer_new_mission,
            requires_priority_reassessment=(
                requires_priority_reassessment
            ),
            rationale=" ".join(
                part
                for part in rationale_parts
                if part
            ),
        )

    @staticmethod
    def _difficulty(
        *,
        tasks,
        task_id: str,
    ) -> str | None:
        for task in tasks:
            if task.id == task_id:
                return task.difficulty

        return None
