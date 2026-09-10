"""
Calculador responsável por construir um Benchmark
a partir das métricas de vários jogadores.
"""

from statistics import mean, median, pstdev

from src.performance_engine.models import (
    Benchmark,
    BenchmarkMetric,
    PlayerMetrics,
)


class BenchmarkCalculator:
    """
    Calcula um benchmark utilizando uma coleção de PlayerMetrics.

    Não busca dados na Riot API e não interpreta desempenho.
    Apenas consolida métricas já calculadas.

    Métricas de combate indisponíveis são ignoradas na distribuição.
    Se nenhum jogador possuir um valor válido para uma métrica de combate,
    o benchmark preserva essa métrica como None.
    """

    @staticmethod
    def calculate(
        metrics: list[PlayerMetrics],
        *,
        name: str,
        total_matches: int,
    ) -> Benchmark:
        """
        Constrói um benchmark a partir das métricas recebidas.
        """

        if not metrics:
            raise ValueError(
                "É necessário informar ao menos uma métrica de jogador."
            )

        if not name.strip():
            raise ValueError(
                "O nome do benchmark deve ser informado."
            )

        if total_matches < 1:
            raise ValueError(
                "O total de partidas deve ser maior que zero."
            )

        average_level_values = [
            item.general.average_level
            for item in metrics
        ]

        placement_deviation_values = [
            item.consistency.placement_standard_deviation
            for item in metrics
        ]

        average_damage_values = [
            item.combat.average_damage_to_players
            for item in metrics
        ]

        average_eliminations_values = [
            item.combat.average_players_eliminated
            for item in metrics
        ]

        return Benchmark(
            name=name.strip(),
            players_analyzed=len(metrics),
            matches_analyzed=total_matches,

            average_placement=round(
                mean(
                    item.general.average_placement
                    for item in metrics
                ),
                2,
            ),

            top4_rate=round(
                mean(
                    item.general.top4_rate
                    for item in metrics
                ),
                2,
            ),

            win_rate=round(
                mean(
                    item.general.win_rate
                    for item in metrics
                ),
                2,
            ),

            average_level=BenchmarkCalculator._build_metric(
                average_level_values
            ),

            placement_standard_deviation=(
                BenchmarkCalculator._build_metric(
                    placement_deviation_values
                )
            ),

            bottom4_rate=round(
                mean(
                    item.consistency.bottom4_rate
                    for item in metrics
                ),
                2,
            ),

            average_damage_to_players=(
                BenchmarkCalculator._build_optional_metric(
                    average_damage_values
                )
            ),

            average_players_eliminated=(
                BenchmarkCalculator._build_optional_metric(
                    average_eliminations_values
                )
            ),

            average_gold_left=round(
                mean(
                    item.economy.average_gold_left
                    for item in metrics
                ),
                2,
            ),
        )

    @staticmethod
    def _build_optional_metric(
        values: list[float | None],
    ) -> BenchmarkMetric | None:
        """
        Constrói uma distribuição usando apenas valores disponíveis.

        None significa dado indisponível e nunca é convertido para zero.
        """
        available_values = [
            value
            for value in values
            if value is not None
        ]

        if not available_values:
            return None

        return BenchmarkCalculator._build_metric(
            available_values
        )

    @staticmethod
    def _build_metric(
        values: list[float],
    ) -> BenchmarkMetric:
        """
        Constrói a distribuição estatística de uma métrica.
        """

        if not values:
            raise ValueError(
                "É necessário informar ao menos um valor."
            )

        ordered_values = sorted(values)

        return BenchmarkMetric(
            mean=round(mean(ordered_values), 2),
            median=round(median(ordered_values), 2),
            standard_deviation=round(
                pstdev(ordered_values),
                2,
            ),
            first_quartile=round(
                BenchmarkCalculator._percentile(
                    ordered_values,
                    0.25,
                ),
                2,
            ),
            third_quartile=round(
                BenchmarkCalculator._percentile(
                    ordered_values,
                    0.75,
                ),
                2,
            ),
            minimum=round(min(ordered_values), 2),
            maximum=round(max(ordered_values), 2),
        )

    @staticmethod
    def _percentile(
        ordered_values: list[float],
        percentile: float,
    ) -> float:
        """
        Calcula um percentil utilizando interpolação linear.

        A lista recebida deve estar ordenada.
        """

        if not ordered_values:
            raise ValueError(
                "A lista de valores não pode ser vazia."
            )

        if not 0.0 <= percentile <= 1.0:
            raise ValueError(
                "O percentil deve estar entre 0 e 1."
            )

        if len(ordered_values) == 1:
            return ordered_values[0]

        position = percentile * (len(ordered_values) - 1)

        lower_index = int(position)
        upper_index = min(
            lower_index + 1,
            len(ordered_values) - 1,
        )

        fraction = position - lower_index

        lower_value = ordered_values[lower_index]
        upper_value = ordered_values[upper_index]

        return lower_value + (
            upper_value - lower_value
        ) * fraction
