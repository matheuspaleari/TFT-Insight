"""
Base de conhecimento pedagógica do Training Engine.
"""

from .board_pressure_tasks import BOARD_PRESSURE_TASKS
from .consistency_tasks import CONSISTENCY_TASKS
from .economy_tasks import ECONOMY_TASKS
from .leveling_tasks import LEVELING_TASKS

TRAINING_TASK_CATALOG = {
    "leveling": LEVELING_TASKS,
    "economy": ECONOMY_TASKS,
    "board_pressure": BOARD_PRESSURE_TASKS,
    "consistency": CONSISTENCY_TASKS,
}


def get_tasks_for_skill(
    skill_id: str,
) -> tuple:
    """
    Retorna os exercícios cadastrados para uma Skill.
    """

    normalized_skill_id = skill_id.strip().lower()

    return TRAINING_TASK_CATALOG.get(
        normalized_skill_id,
        (),
    )


__all__ = [
    "BOARD_PRESSURE_TASKS",
    "CONSISTENCY_TASKS",
    "ECONOMY_TASKS",
    "LEVELING_TASKS",
    "TRAINING_TASK_CATALOG",
    "get_tasks_for_skill",
]