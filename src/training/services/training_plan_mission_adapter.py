from __future__ import annotations

from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingTask
from src.training.models.training_plan import TrainingPlan


class TrainingPlanMissionAdapter:
    """
    Seleciona uma TrainingTask existente a partir de um TrainingPlan.

    A responsabilidade deste adapter é reaproveitar o catálogo pedagógico
    existente. Ele não cria uma segunda missão e não altera o progresso.
    """

    EXERCISE_TASK_MAP: dict[str, str] = {
        "leveling_timing_review": "balance_level_and_stability",
        "consistency_decision_checkpoint": "define_simple_game_plan",
    }

    @classmethod
    def select_task(
        cls,
        *,
        training_plan: TrainingPlan,
    ) -> TrainingTask:
        tasks = get_tasks_for_skill(
            training_plan.primary_skill_id
        )

        if not tasks:
            raise RuntimeError(
                "Nenhum exercício foi encontrado para a Skill: "
                f"{training_plan.primary_skill_id}"
            )

        preferred_task_id = cls.EXERCISE_TASK_MAP.get(
            training_plan.exercise.exercise_id
        )

        if preferred_task_id:
            for task in tasks:
                if task.id == preferred_task_id:
                    return task

        return tasks[0]
