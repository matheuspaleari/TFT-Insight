"""
Serviço responsável por gerar missões de treinamento.
"""

from src.learning.models import LearningRecommendation
from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingMission, TrainingTask
from src.training.models.training_plan import TrainingPlan

from .training_plan_mission_adapter import (
    TrainingPlanMissionAdapter,
)


class MissionGenerator:
    """
    Cria a missão sem decidir prioridade.

    O baseline registra as partidas existentes no início do ciclo.
    """

    DEFAULT_GAMES_TARGET = 5

    @classmethod
    def generate(
        cls,
        *,
        recommendation: LearningRecommendation,
        games_target: int = DEFAULT_GAMES_TARGET,
        baseline_match_ids: tuple[str, ...] = (),
    ) -> TrainingMission:
        if games_target < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        task = cls._select_task(
            skill_id=recommendation.skill.id,
        )

        return TrainingMission(
            task=task,
            games_target=games_target,
            baseline_match_ids=tuple(
                baseline_match_ids
            ),
        )

    @classmethod
    def generate_from_plan(
        cls,
        *,
        training_plan: TrainingPlan,
        baseline_match_ids: tuple[str, ...] = (),
    ) -> TrainingMission:
        if training_plan.games_target < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        task = TrainingPlanMissionAdapter.select_task(
            training_plan=training_plan
        )

        return TrainingMission(
            task=task,
            games_target=training_plan.games_target,
            baseline_match_ids=tuple(
                baseline_match_ids
            ),
        )

    @staticmethod
    def _select_task(
        *,
        skill_id: str,
    ) -> TrainingTask:
        tasks = get_tasks_for_skill(
            skill_id,
        )

        if not tasks:
            raise RuntimeError(
                "Nenhum exercício foi encontrado para a Skill: "
                f"{skill_id}"
            )

        return tasks[0]
