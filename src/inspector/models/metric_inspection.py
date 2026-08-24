"""
Modelo que representa a inspeção detalhada de uma métrica.
"""

from dataclasses import dataclass

from src.performance_engine.models import MetricType


@dataclass(slots=True, frozen=True)
class MetricInspection:
    """
    Explica como uma métrica do jogador foi comparada
    com a distribuição estatística do benchmark.
    """

    metric: MetricType

    player_value: float

    benchmark_mean: float
    benchmark_median: float
    benchmark_standard_deviation: float
    benchmark_first_quartile: float
    benchmark_third_quartile: float
    benchmark_minimum: float
    benchmark_maximum: float

    difference_from_mean: float
    z_score: float
    percentile: float

    score: float
    weight: float

    higher_is_better: bool

    @property
    def metric_id(self) -> str:
        return self.metric.value

    @property
    def weighted_impact(self) -> float:
        """
        Retorna a contribuição ponderada da métrica.
        """

        return round(
            self.score * self.weight,
            2,
        )

    @property
    def position_label(self) -> str:
        """
        Retorna uma descrição relativa ao benchmark.

        Não classifica a habilidade absoluta do jogador.
        """

        if self.percentile < 10.0:
            return "Bem abaixo da referência"

        if self.percentile < 30.0:
            return "Abaixo da referência"

        if self.percentile < 70.0:
            return "Próximo da referência"

        if self.percentile < 90.0:
            return "Acima da referência"

        return "Entre os melhores resultados da referência"