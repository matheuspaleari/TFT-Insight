"""
Calculador responsável por comparar uma métrica do jogador
com a distribuição estatística de um benchmark.
"""

from math import erf, sqrt

from src.performance_engine.models import (
    BenchmarkMetric,
    MetricEvaluation,
    MetricType,
)


class MetricEvaluator:
    """
    Avalia uma métrica utilizando Z-Score.

    O Z-Score é convertido para um percentil entre 0 e 100
    utilizando a função de distribuição acumulada normal.
    """

    @staticmethod
    def evaluate(
        *,
        metric: MetricType,
        player_value: float,
        benchmark_metric: BenchmarkMetric,
        weight: float,
        higher_is_better: bool = True,
    ) -> MetricEvaluation:
        """
        Compara o valor do jogador com o benchmark.

        Args:
            metric: Tipo da métrica avaliada.
            player_value: Valor obtido pelo jogador.
            benchmark_metric: Distribuição estatística da referência.
            weight: Peso da métrica no score final.
            higher_is_better: Indica se valores maiores representam
                melhor desempenho.

        Returns:
            Resultado da avaliação da métrica.
        """

        if not 0.0 <= weight <= 1.0:
            raise ValueError(
                "O peso deve estar entre 0 e 1."
            )

        z_score = MetricEvaluator._calculate_z_score(
            player_value=player_value,
            benchmark_metric=benchmark_metric,
        )

        if not higher_is_better:
            z_score *= -1

        score = MetricEvaluator._z_score_to_percentile(
            z_score
        )

        return MetricEvaluation(
            metric=metric,
            player_value=round(player_value, 2),
            benchmark_metric=benchmark_metric,
            score=round(score, 2),
            weight=weight,
        )

    @staticmethod
    def _calculate_z_score(
        *,
        player_value: float,
        benchmark_metric: BenchmarkMetric,
    ) -> float:
        """
        Calcula quantos desvios padrão o valor do jogador
        está distante da média do benchmark.
        """

        standard_deviation = (
            benchmark_metric.standard_deviation
        )

        if standard_deviation == 0:
            if player_value == benchmark_metric.mean:
                return 0.0

            return (
                float("inf")
                if player_value > benchmark_metric.mean
                else float("-inf")
            )

        return (
            player_value - benchmark_metric.mean
        ) / standard_deviation

    @staticmethod
    def _z_score_to_percentile(
        z_score: float,
    ) -> float:
        """
        Converte um Z-Score para percentil entre 0 e 100.
        """

        percentile = 0.5 * (
            1.0 + erf(z_score / sqrt(2.0))
        )

        return percentile * 100.0