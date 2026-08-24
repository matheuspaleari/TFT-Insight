from dataclasses import dataclass, field
from typing import Any

from .metric_evaluation import MetricEvaluation
from .priority import Priority


@dataclass(slots=True)
class Performance:
    """
    Representa o resultado final produzido pelo Performance Engine.
    """

    score: float
    status: str

    potential_score: float | None = None

    evaluations: list[MetricEvaluation] = field(
        default_factory=list
    )

    priorities: list[Priority] = field(
        default_factory=list
    )

    matches_analyzed: int = 0
    benchmark_name: str = ""

    def __post_init__(self) -> None:
        self.score = self._normalize_score(
            self.score,
            decimal_places=1,
        )

        if self.potential_score is not None:
            self.potential_score = self._normalize_score(
                self.potential_score,
                decimal_places=1,
            )

        if self.matches_analyzed < 0:
            raise ValueError(
                "Performance.matches_analyzed não pode ser negativo."
            )

        if not self.status.strip():
            raise ValueError(
                "Performance.status não pode ser vazio."
            )

        self.status = self.status.strip()
        self.benchmark_name = self.benchmark_name.strip()

        self.evaluations = sorted(
            self.evaluations,
            key=lambda evaluation: evaluation.weight,
            reverse=True,
        )

        self.priorities = sorted(
            self.priorities,
            key=lambda priority: priority.rank,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte a Performance em um dicionário serializável.
        """

        return {
            "score": self.score,
            "status": self.status,
            "potential_score": self.potential_score,
            "evaluations": [
                evaluation.to_dict()
                for evaluation in self.evaluations
            ],
            "priorities": [
                priority.to_dict()
                for priority in self.priorities
            ],
            "matches_analyzed": self.matches_analyzed,
            "benchmark_name": self.benchmark_name,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Performance":
        """
        Reconstrói uma Performance a partir de um dicionário.
        """

        potential_score = data.get("potential_score")

        return cls(
            score=float(data["score"]),
            status=str(data["status"]),
            potential_score=(
                float(potential_score)
                if potential_score is not None
                else None
            ),
            evaluations=[
                MetricEvaluation.from_dict(item)
                for item in data.get("evaluations", [])
            ],
            priorities=[
                Priority.from_dict(item)
                for item in data.get("priorities", [])
            ],
            matches_analyzed=int(
                data["matches_analyzed"]
            ),
            benchmark_name=str(
                data["benchmark_name"]
            ),
        )

    @staticmethod
    def _normalize_score(
        value: float,
        *,
        decimal_places: int,
    ) -> float:
        normalized_value = max(
            0.0,
            min(100.0, float(value)),
        )

        return round(
            normalized_value,
            decimal_places,
        )

    @property
    def main_priority(self) -> Priority | None:
        return (
            self.priorities[0]
            if self.priorities
            else None
        )