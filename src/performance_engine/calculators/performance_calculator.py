"""
Calculador responsável por consolidar a performance
do jogador em comparação ao benchmark.
"""

from src.performance_engine.models import (
    Benchmark,
    MetricEvaluation,
    MetricType,
    Performance,
    PlayerMetrics,
)

from .metric_evaluator import MetricEvaluator


class PerformanceCalculator:
    """
    Calcula a nota consolidada de performance do jogador.
    """

    @staticmethod
    def calculate(
        *,
        player_metrics: PlayerMetrics,
        benchmark: Benchmark,
        performance_weights: dict[MetricType, float],
        status: str = "Avaliado",
    ) -> Performance:
        """
        Compara as métricas do jogador com o benchmark
        utilizando os pesos do perfil competitivo selecionado.
        """

        PerformanceCalculator._validate_weights(
            performance_weights
        )

        evaluations = (
            PerformanceCalculator._build_evaluations(
                player_metrics=player_metrics,
                benchmark=benchmark,
                performance_weights=performance_weights,
            )
        )

        overall_score = (
            PerformanceCalculator._calculate_weighted_score(
                evaluations
            )
        )

        return Performance(
            score=overall_score,
            status=status,
            evaluations=evaluations,
            matches_analyzed=(
                player_metrics.general.matches_played
            ),
            benchmark_name=benchmark.name,
        )

    @staticmethod
    def _build_evaluations(
        *,
        player_metrics: PlayerMetrics,
        benchmark: Benchmark,
        performance_weights: dict[MetricType, float],
    ) -> list[MetricEvaluation]:
        """
        Avalia individualmente cada métrica.
        """

        players_eliminated = MetricEvaluator.evaluate(
            metric=MetricType.PLAYERS_ELIMINATED,
            player_value=(
                player_metrics
                .combat
                .average_players_eliminated
            ),
            benchmark_metric=(
                benchmark.average_players_eliminated
            ),
            weight=performance_weights[
                MetricType.PLAYERS_ELIMINATED
            ],
        )

        damage_to_players = MetricEvaluator.evaluate(
            metric=MetricType.DAMAGE_TO_PLAYERS,
            player_value=(
                player_metrics
                .combat
                .average_damage_to_players
            ),
            benchmark_metric=(
                benchmark.average_damage_to_players
            ),
            weight=performance_weights[
                MetricType.DAMAGE_TO_PLAYERS
            ],
        )

        level = MetricEvaluator.evaluate(
            metric=MetricType.LEVEL,
            player_value=(
                player_metrics.general.average_level
            ),
            benchmark_metric=benchmark.average_level,
            weight=performance_weights[
                MetricType.LEVEL
            ],
        )

        consistency = MetricEvaluator.evaluate(
            metric=MetricType.CONSISTENCY,
            player_value=(
                player_metrics
                .consistency
                .placement_standard_deviation
            ),
            benchmark_metric=(
                benchmark.placement_standard_deviation
            ),
            weight=performance_weights[
                MetricType.CONSISTENCY
            ],
            higher_is_better=False,
        )

        return [
            players_eliminated,
            damage_to_players,
            level,
            consistency,
        ]

    @staticmethod
    def _calculate_weighted_score(
        evaluations: list[MetricEvaluation],
    ) -> float:
        """
        Calcula a média ponderada dos scores individuais.
        """

        if not evaluations:
            raise ValueError(
                "É necessário informar ao menos uma avaliação."
            )

        total_weight = sum(
            evaluation.weight
            for evaluation in evaluations
        )

        if total_weight <= 0:
            raise ValueError(
                "A soma dos pesos deve ser maior que zero."
            )

        weighted_score = sum(
            evaluation.score * evaluation.weight
            for evaluation in evaluations
        )

        return weighted_score / total_weight

    @staticmethod
    def _validate_weights(
        performance_weights: dict[MetricType, float],
    ) -> None:
        """
        Valida se todas as métricas necessárias possuem peso.
        """

        required_metrics = {
            MetricType.PLAYERS_ELIMINATED,
            MetricType.DAMAGE_TO_PLAYERS,
            MetricType.LEVEL,
            MetricType.CONSISTENCY,
        }

        missing_metrics = (
            required_metrics
            - performance_weights.keys()
        )

        if missing_metrics:
            missing_names = ", ".join(
                sorted(
                    metric.value
                    for metric in missing_metrics
                )
            )

            raise ValueError(
                "Pesos ausentes para as métricas: "
                f"{missing_names}."
            )

        total_weight = sum(
            performance_weights.values()
        )

        if abs(total_weight - 1.0) > 0.000001:
            raise ValueError(
                "A soma dos pesos de Performance "
                "deve ser igual a 1."
            )