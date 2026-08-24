"""
Modelo que representa uma missão ativa de treinamento.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .training_task import TrainingTask


@dataclass(slots=True, frozen=True)
class TrainingMission:
    """
    Representa um exercício atribuído ao jogador.

    `baseline_match_ids` guarda as partidas que já existiam quando
    a missão começou. Apenas partidas posteriores a esse baseline
    podem avançar o ciclo.
    """

    task: TrainingTask

    games_target: int = 5
    games_completed: int = 0

    mission_id: str = ""
    created_at: str = ""

    baseline_match_ids: tuple[str, ...] = field(
        default_factory=tuple,
    )

    completed_match_ids: tuple[str, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self) -> None:
        if self.games_target < 1:
            raise ValueError(
                "TrainingMission.games_target deve ser maior que zero."
            )

        if self.games_completed < 0:
            raise ValueError(
                "TrainingMission.games_completed não pode ser negativo."
            )

        if self.games_completed > self.games_target:
            raise ValueError(
                "TrainingMission.games_completed não pode ser maior que games_target."
            )

        if self.games_completed != len(
            self.completed_match_ids
        ):
            raise ValueError(
                "TrainingMission.games_completed deve ser igual "
                "à quantidade de completed_match_ids."
            )

        if len(set(self.baseline_match_ids)) != len(
            self.baseline_match_ids
        ):
            raise ValueError(
                "TrainingMission.baseline_match_ids não pode "
                "possuir partidas duplicadas."
            )

        if len(set(self.completed_match_ids)) != len(
            self.completed_match_ids
        ):
            raise ValueError(
                "TrainingMission.completed_match_ids não pode "
                "possuir partidas duplicadas."
            )

        overlap = (
            set(self.baseline_match_ids)
            & set(self.completed_match_ids)
        )

        if overlap:
            raise ValueError(
                "Uma partida não pode pertencer ao baseline e "
                "ao progresso da mesma missão."
            )

        if not self.mission_id:
            object.__setattr__(
                self,
                "mission_id",
                str(uuid4()),
            )

        if not self.created_at:
            object.__setattr__(
                self,
                "created_at",
                datetime.now(
                    timezone.utc,
                ).isoformat(),
            )

    @property
    def skill_id(self) -> str:
        return self.task.skill_id

    @property
    def title(self) -> str:
        return self.task.title

    @property
    def is_completed(self) -> bool:
        return self.games_completed >= self.games_target

    @property
    def remaining_games(self) -> int:
        return max(
            0,
            self.games_target - self.games_completed,
        )

    @property
    def progress_percentage(self) -> float:
        progress = (
            self.games_completed
            / self.games_target
        ) * 100.0

        return round(
            progress,
            1,
        )

    @property
    def progress_bar(self) -> str:
        completed = "■" * self.games_completed
        remaining = "□" * self.remaining_games

        return completed + remaining

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "created_at": self.created_at,
            "games_target": self.games_target,
            "games_completed": self.games_completed,
            "baseline_match_ids": list(
                self.baseline_match_ids
            ),
            "completed_match_ids": list(
                self.completed_match_ids
            ),
            "task": self.task.to_dict(),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "TrainingMission":
        task_data = data["task"]

        if not isinstance(task_data, dict):
            raise TypeError(
                "TrainingMission.task deve ser um dicionário."
            )

        return cls(
            task=TrainingTask.from_dict(
                task_data
            ),
            games_target=int(
                data["games_target"]
            ),
            games_completed=int(
                data.get(
                    "games_completed",
                    0,
                )
            ),
            mission_id=str(
                data["mission_id"]
            ),
            created_at=str(
                data["created_at"]
            ),
            # Retrocompatibilidade: missões antigas não possuem baseline.
            baseline_match_ids=tuple(
                str(item)
                for item in data.get(
                    "baseline_match_ids",
                    [],
                )
            ),
            completed_match_ids=tuple(
                str(item)
                for item in data.get(
                    "completed_match_ids",
                    [],
                )
            ),
        )
