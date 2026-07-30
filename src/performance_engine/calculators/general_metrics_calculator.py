from statistics import mean

from src.performance_engine.models import GeneralMetrics, Match


class GeneralMetricsCalculator:
    """
    Calcula métricas gerais a partir de uma lista de partidas.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> GeneralMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        placements = [match.placement for match in matches]
        levels = [match.level for match in matches]

        matches_played = len(matches)

        top4_count = sum(
            1
            for placement in placements
            if placement <= 4
        )

        win_count = sum(
            1
            for placement in placements
            if placement == 1
        )

        return GeneralMetrics(
            matches_played=matches_played,
            average_placement=round(mean(placements), 2),
            top4_rate=round(
                top4_count / matches_played * 100,
                2,
            ),
            win_rate=round(
                win_count / matches_played * 100,
                2,
            ),
            average_level=round(mean(levels), 2),
        )