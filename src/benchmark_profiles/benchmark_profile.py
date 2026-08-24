"""
Modelo de configuração de um benchmark.
"""

from dataclasses import dataclass

from src.performance_engine.models import MetricType


@dataclass(slots=True, frozen=True)
class BenchmarkProfile:
    """
    Define como o sistema deve se comportar para um benchmark.
    """

    id: str

    performance_weights: dict[
        MetricType,
        float,
    ]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "BenchmarkProfile.id não pode ser vazio."
            )

        if not self.performance_weights:
            raise ValueError(
                "BenchmarkProfile.performance_weights "
                "não pode ser vazio."
            )

        total_weight = sum(
            self.performance_weights.values()
        )

        if abs(total_weight - 1.0) > 0.000001:
            raise ValueError(
                "A soma dos pesos de Performance "
                "deve ser igual a 1."
            )