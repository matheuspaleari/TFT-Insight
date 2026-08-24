"""
Domínio de treinamento do TFT Insight.

Os serviços são carregados sob demanda para evitar dependências
circulares com o PlayerRepository.
"""

from typing import Any

from .models import (
    TrainingMission,
    TrainingTask,
)


__all__ = [
    "MissionGenerator",
    "PlayerTrainingService",
    "TrainingMission",
    "TrainingTask",
]


def __getattr__(name: str) -> Any:
    if name == "MissionGenerator":
        from .services import MissionGenerator

        return MissionGenerator

    if name == "PlayerTrainingService":
        from .services import PlayerTrainingService

        return PlayerTrainingService

    raise AttributeError(
        f"O módulo {__name__!r} não possui o atributo {name!r}."
    )