from statistics import pstdev, pvariance

from src.performance_engine.models import ConsistencyMetrics, Match


class ConsistencyMetricsCalculator:
    """
    Calcula a consistência dos resultados do jogador.

    Usa a variância e o desvio-padrão populacionais porque as partidas
    recebidas representam todo o período que está sendo analisado.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> ConsistencyMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        placements = [match.placement for match in matches]
        matches_played = len(matches)

        bottom4_count = sum(
            1
            for placement in placements
            if placement >= 5
        )

        return ConsistencyMetrics(
            placement_variance=round(
                pvariance(placements),
                2,
            ),
            placement_standard_deviation=round(
                pstdev(placements),
                2,
            ),
            bottom4_rate=round(
                bottom4_count / matches_played * 100,
                2,
            ),
            best_placement=min(placements),
            worst_placement=max(placements),
        )