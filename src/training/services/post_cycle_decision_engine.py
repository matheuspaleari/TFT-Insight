from __future__ import annotations

from typing import Any

from src.training.models.post_cycle_decision import (
    PostCycleDecision,
)


class PostCycleDecisionEngine:
    """
    Decide como transformar a prioridade atual em próximo ciclo.

    Importante:
    - NÃO escolhe a Skill prioritária.
    - recebe a prioridade já decidida pelo Learning Priority Engine.
    - usa o histórico apenas para decidir COMO treinar essa Skill.
    - um resultado negativo não prende o jogador eternamente na mesma Skill.
    """

    TASK_CATALOG: dict[str, tuple[str, ...]] = {
        "leveling": (
            "plan_level_before_spending",
            "balance_level_and_stability",
            "avoid_unplanned_rerolls",
        ),
        "consistency": (
            "define_simple_game_plan",
            "review_one_decision_per_match",
            "reduce_unnecessary_risk",
        ),
    }

    @classmethod
    def decide(
        cls,
        *,
        priority_skill_id: str,
        completed_mission: dict[str, Any] | None,
        training_history: list[dict[str, Any]],
    ) -> PostCycleDecision:
        target_skill = str(
            priority_skill_id
        ).strip()

        if not target_skill:
            raise ValueError(
                "priority_skill_id não pode ser vazio."
            )

        completed_skill = cls._mission_skill_id(
            completed_mission
        )

        target_history = cls._cycles_for_skill(
            training_history=training_history,
            skill_id=target_skill,
        )

        latest_target_cycle = (
            target_history[0]
            if target_history
            else None
        )

        previous_task_id = cls._cycle_task_id(
            latest_target_cycle
        )

        previous_result = cls._evaluation_value(
            latest_target_cycle,
            "result",
        )

        previous_confidence = cls._evaluation_value(
            latest_target_cycle,
            "confidence",
        )

        # A prioridade nova sempre vence o histórico.
        if (
            completed_skill
            and completed_skill != target_skill
        ):
            action = "CHANGE_PRIORITY"
        elif completed_skill == target_skill:
            action = cls._same_skill_action(
                previous_result=previous_result
            )
        else:
            action = "START_PRIORITY"

        (
            task_strategy,
            suggested_task_id,
            excluded_task_ids,
        ) = cls._task_strategy(
            skill_id=target_skill,
            previous_task_id=previous_task_id,
            previous_result=previous_result,
            history=target_history,
        )

        rationale = cls._rationale(
            action=action,
            target_skill_id=target_skill,
            completed_skill_id=completed_skill,
            previous_result=previous_result,
            previous_confidence=previous_confidence,
            previous_task_id=previous_task_id,
            task_strategy=task_strategy,
            suggested_task_id=suggested_task_id,
        )

        return PostCycleDecision(
            action=action,
            target_skill_id=target_skill,
            previous_skill_id=completed_skill,
            previous_task_id=previous_task_id,
            previous_result=previous_result,
            previous_confidence=previous_confidence,
            task_strategy=task_strategy,
            suggested_task_id=suggested_task_id,
            excluded_task_ids=excluded_task_ids,
            rationale=rationale,
            history_used=latest_target_cycle is not None,
        )

    @staticmethod
    def _same_skill_action(
        *,
        previous_result: str | None,
    ) -> str:
        result = (
            str(previous_result).upper()
            if previous_result
            else ""
        )

        if result == "INCONCLUSIVE":
            return "RETRY_TASK"

        if result == "POSITIVE":
            return "ADVANCE_SKILL"

        return "REPEAT_SKILL"

    @classmethod
    def _task_strategy(
        cls,
        *,
        skill_id: str,
        previous_task_id: str | None,
        previous_result: str | None,
        history: list[dict[str, Any]],
    ) -> tuple[str, str | None, tuple[str, ...]]:
        catalog = cls.TASK_CATALOG.get(
            skill_id,
            (),
        )

        if not catalog:
            return (
                "DEFAULT_TASK",
                None,
                (),
            )

        used_task_ids = tuple(
            task_id
            for task_id in (
                cls._cycle_task_id(cycle)
                for cycle in history
            )
            if task_id
        )

        result = (
            str(previous_result).upper()
            if previous_result
            else ""
        )

        # Resultado inconclusivo: repetir o mesmo exercício pode produzir
        # uma segunda janela comparável, em vez de trocar a variável.
        if (
            result == "INCONCLUSIVE"
            and previous_task_id in catalog
        ):
            return (
                "RETRY_SAME_TASK",
                previous_task_id,
                (),
            )

        # Para NEGATIVE/STABLE/POSITIVE, evita repetir imediatamente.
        # Prioriza exercício ainda não usado naquela Skill.
        for task_id in catalog:
            if task_id not in used_task_ids:
                return (
                    "ROTATE_TASK",
                    task_id,
                    (
                        previous_task_id,
                    )
                    if previous_task_id
                    else (),
                )

        # Todos já foram usados: faz rotação circular.
        if (
            previous_task_id
            and previous_task_id in catalog
        ):
            current_index = catalog.index(
                previous_task_id
            )
            next_index = (
                current_index + 1
            ) % len(catalog)

            return (
                "ROTATE_TASK",
                catalog[next_index],
                (previous_task_id,),
            )

        return (
            "DEFAULT_TASK",
            catalog[0],
            (),
        )

    @staticmethod
    def _mission_skill_id(
        mission: dict[str, Any] | None,
    ) -> str | None:
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

    @staticmethod
    def _cycle_task_id(
        cycle: dict[str, Any] | None,
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
                "id",
                "",
            )
        ).strip()

        return value or None

    @staticmethod
    def _cycle_skill_id(
        cycle: dict[str, Any] | None,
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

    @classmethod
    def _cycles_for_skill(
        cls,
        *,
        training_history: list[dict[str, Any]],
        skill_id: str,
    ) -> list[dict[str, Any]]:
        return [
            cycle
            for cycle in training_history
            if cls._cycle_skill_id(
                cycle
            ) == skill_id
        ]

    @staticmethod
    def _evaluation_value(
        cycle: dict[str, Any] | None,
        key: str,
    ) -> str | None:
        if not isinstance(
            cycle,
            dict,
        ):
            return None

        evaluation = cycle.get(
            "evaluation",
            {},
        )

        if not isinstance(
            evaluation,
            dict,
        ):
            return None

        value = str(
            evaluation.get(
                key,
                "",
            )
        ).strip()

        return value or None

    @staticmethod
    def _rationale(
        *,
        action: str,
        target_skill_id: str,
        completed_skill_id: str | None,
        previous_result: str | None,
        previous_confidence: str | None,
        previous_task_id: str | None,
        task_strategy: str,
        suggested_task_id: str | None,
    ) -> str:
        parts: list[str] = []

        if action == "CHANGE_PRIORITY":
            parts.append(
                "A análise atual definiu uma Skill diferente da missão "
                "que acabou de ser concluída; a prioridade atual é preservada."
            )
        elif action == "RETRY_TASK":
            parts.append(
                "A prioridade continua na mesma Skill e o último resultado "
                "foi inconclusivo."
            )
        elif action == "ADVANCE_SKILL":
            parts.append(
                "A prioridade continua na mesma Skill após um ciclo com "
                "mudança positiva observada."
            )
        elif action == "REPEAT_SKILL":
            parts.append(
                "A prioridade continua na mesma Skill, portanto um novo "
                "ciclo ainda é pertinente."
            )
        else:
            parts.append(
                "A prioridade atual não possui uma missão concluída "
                "imediatamente anterior para comparar."
            )

        if previous_result:
            parts.append(
                "O histórico mais recente da Skill-alvo registrou "
                f"{previous_result}"
                + (
                    f" com confiança {previous_confidence}."
                    if previous_confidence
                    else "."
                )
            )

        if (
            task_strategy == "ROTATE_TASK"
            and suggested_task_id
        ):
            parts.append(
                "O histórico não altera a prioridade; ele apenas evita "
                "repetir imediatamente o mesmo exercício e sugere "
                f"{suggested_task_id}."
            )
        elif (
            task_strategy == "RETRY_SAME_TASK"
            and previous_task_id
        ):
            parts.append(
                "Como a evidência anterior foi inconclusiva, o mesmo "
                f"exercício ({previous_task_id}) é mantido para gerar "
                "uma nova janela comparável."
            )

        return " ".join(
            parts
        )
