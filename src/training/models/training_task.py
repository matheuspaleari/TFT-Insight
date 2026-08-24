"""
Modelo que representa um exercício de treinamento.

O objetivo deste modelo não é representar uma missão em andamento,
mas um exercício pedagógico utilizado pelo Training Engine.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class TrainingTask:
    """
    Exercício pedagógico associado a uma Skill.
    """

    id: str
    skill_id: str

    title: str
    description: str

    objective: str
    habit: str

    checklist: tuple[str, ...] = field(
        default_factory=tuple,
    )

    success_signals: tuple[str, ...] = field(
        default_factory=tuple,
    )

    common_mistakes: tuple[str, ...] = field(
        default_factory=tuple,
    )

    related_metric_ids: tuple[str, ...] = field(
        default_factory=tuple,
    )

    difficulty: str = "FOUNDATION"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "TrainingTask.id não pode ser vazio."
            )

        if not self.skill_id.strip():
            raise ValueError(
                "TrainingTask.skill_id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "TrainingTask.title não pode ser vazio."
            )

        if not self.description.strip():
            raise ValueError(
                "TrainingTask.description não pode ser vazia."
            )

        if not self.objective.strip():
            raise ValueError(
                "TrainingTask.objective não pode ser vazio."
            )

        if not self.habit.strip():
            raise ValueError(
                "TrainingTask.habit não pode ser vazio."
            )

        if not self.checklist:
            raise ValueError(
                "TrainingTask.checklist deve possuir "
                "ao menos um item."
            )

        if not self.success_signals:
            raise ValueError(
                "TrainingTask.success_signals deve possuir "
                "ao menos um item."
            )

        allowed_difficulties = {
            "FOUNDATION",
            "INTERMEDIATE",
            "ADVANCED",
        }

        if self.difficulty not in allowed_difficulties:
            raise ValueError(
                "TrainingTask.difficulty deve ser FOUNDATION, "
                "INTERMEDIATE ou ADVANCED."
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte o exercício em um dicionário serializável.
        """

        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "title": self.title,
            "description": self.description,
            "objective": self.objective,
            "habit": self.habit,
            "checklist": list(self.checklist),
            "success_signals": list(
                self.success_signals
            ),
            "common_mistakes": list(
                self.common_mistakes
            ),
            "related_metric_ids": list(
                self.related_metric_ids
            ),
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "TrainingTask":
        """
        Reconstrói um exercício a partir de um dicionário.
        """

        return cls(
            id=str(data["id"]),
            skill_id=str(data["skill_id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            objective=str(data["objective"]),
            habit=str(data["habit"]),
            checklist=tuple(
                str(item)
                for item in data.get("checklist", [])
            ),
            success_signals=tuple(
                str(item)
                for item in data.get(
                    "success_signals",
                    [],
                )
            ),
            common_mistakes=tuple(
                str(item)
                for item in data.get(
                    "common_mistakes",
                    [],
                )
            ),
            related_metric_ids=tuple(
                str(item)
                for item in data.get(
                    "related_metric_ids",
                    [],
                )
            ),
        )