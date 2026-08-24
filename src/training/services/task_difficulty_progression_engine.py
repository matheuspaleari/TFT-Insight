from __future__ import annotations

from src.training.knowledge import get_tasks_for_skill
from src.training.models.task_progression_decision import (
    TASK_DIFFICULTY_ORDER,
    TaskProgressionDecision,
)


class TaskDifficultyProgressionEngine:
    """
    Fase 10.4.

    Converte o sinal pedagógico do AntiLoopTrainingGuard em uma seleção
    determinística de task dentro da Skill.

    Este engine NÃO escolhe a Skill. Ele recebe skill_id já definido.
    """

    VALID_SIGNALS = {
        "HOLD",
        "ROTATE",
        "ADVANCE_CANDIDATE",
        "PAUSE_AND_REASSESS",
    }

    @classmethod
    def decide(
        cls,
        *,
        skill_id: str,
        current_task_id: str,
        progression_signal: str,
    ) -> TaskProgressionDecision:
        signal = str(
            progression_signal
        ).strip().upper()

        if signal not in cls.VALID_SIGNALS:
            raise ValueError(
                "progression_signal inválido: "
                f"{progression_signal}"
            )

        tasks = tuple(
            get_tasks_for_skill(
                skill_id
            )
        )

        if not tasks:
            raise RuntimeError(
                "Nenhuma task cadastrada para a Skill: "
                f"{skill_id}"
            )

        current = next(
            (
                task
                for task in tasks
                if task.id == current_task_id
            ),
            None,
        )

        if current is None:
            raise RuntimeError(
                "Task atual não encontrada no catálogo: "
                f"{skill_id}/{current_task_id}"
            )

        selected, rationale = cls._select(
            tasks=tasks,
            current=current,
            signal=signal,
        )

        return TaskProgressionDecision(
            skill_id=skill_id,
            progression_signal=signal,
            current_task_id=current.id,
            current_difficulty=current.difficulty,
            selected_task_id=selected.id,
            selected_difficulty=selected.difficulty,
            changed_task=selected.id != current.id,
            changed_difficulty=(
                selected.difficulty
                != current.difficulty
            ),
            rationale=rationale,
        )

    @classmethod
    def _select(
        cls,
        *,
        tasks,
        current,
        signal: str,
    ):
        if signal == "HOLD":
            return (
                current,
                "O histórico ainda não justifica mudar exercício ou dificuldade.",
            )

        if signal == "ADVANCE_CANDIDATE":
            candidate = cls._next_harder(
                tasks=tasks,
                current=current,
            )

            if candidate is None:
                return (
                    current,
                    "A task atual já está no maior nível de dificuldade disponível.",
                )

            return (
                candidate,
                (
                    "A tendência positiva permite avançar para a próxima "
                    "dificuldade disponível dentro da mesma Skill."
                ),
            )

        if signal == "PAUSE_AND_REASSESS":
            foundation = cls._foundation_task(
                tasks
            )

            return (
                foundation,
                (
                    "A reavaliação pedagógica retorna ao exercício FOUNDATION "
                    "da Skill antes de uma nova tentativa."
                ),
            )

        # ROTATE:
        # 1) prefere outra task de mesma dificuldade;
        # 2) depois uma task mais fácil;
        # 3) nunca sobe dificuldade por causa de um sinal ROTATE;
        # 4) se não houver alternativa segura, mantém a atual.
        same_level = [
            task
            for task in tasks
            if (
                task.id != current.id
                and task.difficulty
                == current.difficulty
            )
        ]

        if same_level:
            return (
                same_level[0],
                "A task foi rotacionada sem alterar a dificuldade.",
            )

        easier = [
            task
            for task in tasks
            if (
                task.id != current.id
                and TASK_DIFFICULTY_ORDER[
                    task.difficulty
                ]
                < TASK_DIFFICULTY_ORDER[
                    current.difficulty
                ]
            )
        ]

        if easier:
            easier.sort(
                key=lambda task: TASK_DIFFICULTY_ORDER[
                    task.difficulty
                ],
                reverse=True,
            )

            return (
                easier[0],
                (
                    "Não existe outra task da mesma dificuldade. "
                    "A rotação usa a alternativa imediatamente mais simples "
                    "para não aumentar exigência durante um sinal de cautela."
                ),
            )

        return (
            current,
            (
                "Não existe alternativa segura de mesma ou menor dificuldade. "
                "A task atual é mantida."
            ),
        )

    @staticmethod
    def _foundation_task(
        tasks,
    ):
        foundations = [
            task
            for task in tasks
            if task.difficulty
            == "FOUNDATION"
        ]

        if foundations:
            return foundations[0]

        return min(
            tasks,
            key=lambda task: TASK_DIFFICULTY_ORDER[
                task.difficulty
            ],
        )

    @staticmethod
    def _next_harder(
        *,
        tasks,
        current,
    ):
        current_order = TASK_DIFFICULTY_ORDER[
            current.difficulty
        ]

        harder = [
            task
            for task in tasks
            if TASK_DIFFICULTY_ORDER[
                task.difficulty
            ] > current_order
        ]

        if not harder:
            return None

        harder.sort(
            key=lambda task: TASK_DIFFICULTY_ORDER[
                task.difficulty
            ]
        )

        return harder[0]
