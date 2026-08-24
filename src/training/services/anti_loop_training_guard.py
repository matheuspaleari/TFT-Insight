from __future__ import annotations

from typing import Any

from src.training.models.anti_loop_decision import (
    AntiLoopDecision,
)
from src.training.services.skill_training_history_aggregator import (
    SkillTrainingHistoryAggregator,
)


class AntiLoopTrainingGuard:
    """
    Fase 10.3 + parte segura da 10.4.

    O guard NÃO escolhe a prioridade principal.
    Ele avalia se insistir na Skill-alvo parece pedagogicamente saudável.

    A parte 10.4 desta V1 não escolhe "task difícil" porque o catálogo atual
    ainda não possui nível de dificuldade formal. Em vez disso, retorna uma
    recomendação de progressão:
    - HOLD
    - ROTATE
    - ADVANCE_CANDIDATE
    - PAUSE_AND_REASSESS
    """

    @classmethod
    def evaluate(
        cls,
        *,
        skill_id: str,
        training_history: list[dict[str, Any]],
    ) -> AntiLoopDecision:
        summary = SkillTrainingHistoryAggregator.aggregate(
            skill_id=skill_id,
            training_history=training_history,
        )

        streak = cls._consecutive_skill_cycles(
            skill_id=skill_id,
            training_history=training_history,
        )

        recent_results = tuple(
            cycle.result
            for cycle in summary.cycles[:3]
            if cycle.result
        )

        action, task_progression, rationale = (
            cls._decide(
                summary=summary,
                streak=streak,
                recent_results=recent_results,
            )
        )

        return AntiLoopDecision(
            skill_id=skill_id,
            action=action,
            task_progression=task_progression,
            trend=summary.trend,
            trend_confidence=summary.trend_confidence,
            consecutive_skill_cycles=streak,
            evaluated_cycles=summary.evaluated_cycles,
            conclusive_cycles=summary.conclusive_cycles,
            recent_results=recent_results,
            rationale=rationale,
            caution=(
                "O guard não substitui o Learning Priority Engine. "
                "Ele apenas sinaliza risco de insistência, necessidade de "
                "rotação/reavaliação ou oportunidade de progressão."
            ),
        )

    @classmethod
    def _decide(
        cls,
        *,
        summary,
        streak: int,
        recent_results: tuple[str, ...],
    ) -> tuple[str, str, str]:
        # Pouco histórico: nunca bloqueia.
        if summary.conclusive_cycles < 2:
            if cls._recent_inconclusive_count(
                recent_results
            ) >= 2:
                return (
                    "REASSESS",
                    "PAUSE_AND_REASSESS",
                    (
                        "Ainda não há dois ciclos conclusivos, mas os resultados "
                        "recentes repetidamente inconclusivos indicam que insistir "
                        "sem revisar a forma de medir/treinar pode gerar um loop."
                    ),
                )

            return (
                "CONTINUE",
                "HOLD",
                (
                    "Ainda não existe histórico conclusivo suficiente para "
                    "interromper ou acelerar o treino desta Skill."
                ),
            )

        # Loop claro: 3 ciclos consecutivos na mesma Skill + regressão.
        if (
            streak >= 3
            and summary.trend == "REGRESSING"
        ):
            return (
                "COOLDOWN_SKILL",
                "PAUSE_AND_REASSESS",
                (
                    "A Skill foi treinada por pelo menos três ciclos consecutivos "
                    "e a tendência continua regressiva. Recomenda-se uma pausa "
                    "pedagógica antes de insistir novamente."
                ),
            )

        # Duas evidências negativas conclusivas recentes pedem reavaliação,
        # mesmo antes do cooldown completo.
        if cls._recent_conclusive_pair(
            summary=summary,
        ) == (
            "NEGATIVE",
            "NEGATIVE",
        ):
            return (
                "REASSESS",
                "PAUSE_AND_REASSESS",
                (
                    "Os dois ciclos conclusivos mais recentes terminaram "
                    "NEGATIVE. Antes de repetir a Skill novamente, revise "
                    "exercício, contexto e evidências."
                ),
            )

        # Tendência estável: a Skill pode continuar, mas não repita o mesmo
        # estímulo indefinidamente.
        if (
            summary.trend == "STABLE"
            and streak >= 2
        ):
            return (
                "ROTATE_TASK",
                "ROTATE",
                (
                    "A Skill permanece estável após ciclos repetidos. "
                    "O próximo treino pode continuar na mesma Skill, mas deve "
                    "trocar o exercício para variar o estímulo."
                ),
            )

        # Tendência positiva: não bloqueia e sinaliza oportunidade de progressão.
        if summary.trend == "IMPROVING":
            return (
                "CONTINUE",
                "ADVANCE_CANDIDATE",
                (
                    "Os ciclos conclusivos mais recentes indicam melhora. "
                    "A Skill pode continuar e passa a ser candidata a um "
                    "exercício de maior exigência quando o catálogo suportar "
                    "dificuldade formal."
                ),
            )

        # Regressão sem streak de 3 e sem dupla negativa: mantém cautela e rotação.
        if summary.trend == "REGRESSING":
            return (
                "ROTATE_TASK",
                "ROTATE",
                (
                    "Existe tendência regressiva, mas ainda não há um loop forte "
                    "o suficiente para aplicar cooldown. Evite repetir o mesmo "
                    "exercício imediatamente."
                ),
            )

        return (
            "CONTINUE",
            "HOLD",
            "O histórico atual não exige intervenção adicional.",
        )

    @staticmethod
    def _recent_inconclusive_count(
        recent_results: tuple[str, ...],
    ) -> int:
        return sum(
            result == "INCONCLUSIVE"
            for result in recent_results[:2]
        )

    @staticmethod
    def _recent_conclusive_pair(
        *,
        summary,
    ) -> tuple[str, str] | None:
        conclusive = [
            cycle.result
            for cycle in summary.cycles
            if cycle.is_conclusive
            and cycle.result
        ]

        if len(conclusive) < 2:
            return None

        return (
            conclusive[0],
            conclusive[1],
        )

    @classmethod
    def _consecutive_skill_cycles(
        cls,
        *,
        skill_id: str,
        training_history: list[dict[str, Any]],
    ) -> int:
        """
        Conta quantos ciclos mais recentes, na ordem recebida pelo repository,
        pertencem à mesma Skill.

        list_training_cycles já é tratado pelo restante do projeto como histórico
        do mais recente para o mais antigo. Se a ordem mudar futuramente, este
        método deve ser adaptado para usar timestamp explícito.
        """

        streak = 0

        for cycle in training_history:
            candidate = cls._cycle_skill_id(
                cycle
            )

            if candidate == skill_id:
                streak += 1
                continue

            if streak > 0:
                break

        return streak

    @staticmethod
    def _cycle_skill_id(
        cycle: dict[str, Any],
    ) -> str | None:
        if not isinstance(
            cycle,
            dict,
        ):
            return None

        mission = cycle.get(
            "mission",
            {},
        )

        if not isinstance(
            mission,
            dict,
        ):
            return None

        task = mission.get(
            "task",
            {},
        )

        if not isinstance(
            task,
            dict,
        ):
            return None

        value = str(
            task.get(
                "skill_id",
                "",
            )
        ).strip()

        return value or None
