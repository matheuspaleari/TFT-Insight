from dataclasses import dataclass
from typing import Any

from .benchmark_metric import BenchmarkMetric
from .metric_type import MetricType


@dataclass(slots=True, frozen=True)
class MetricEvaluation:
    """
    Representa a avaliação de uma única métrica do jogador
    em comparação ao benchmark.
    """

    metric: MetricType
    player_value: float
    benchmark_metric: BenchmarkMetric
    score: float
    weight: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "O score deve estar entre 0 e 100."
            )

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                "O peso deve estar entre 0 e 1."
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte a avaliação em um dicionário serializável.
        """

        return {
            "metric": self.metric.value,
            "player_value": self.player_value,
            "benchmark_metric": self.benchmark_metric.to_dict(),
            "score": self.score,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "MetricEvaluation":
        """
        Reconstrói uma avaliação a partir de um dicionário.
        """

        return cls(
            metric=MetricType(str(data["metric"])),
            player_value=float(data["player_value"]),
            benchmark_metric=BenchmarkMetric.from_dict(
                data["benchmark_metric"]
            ),
            score=float(data["score"]),
            weight=float(data["weight"]),
        )