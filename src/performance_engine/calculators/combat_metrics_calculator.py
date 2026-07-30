from statistics import mean

from src.performance_engine.models import CombatMetrics, Match


class CombatMetricsCalculator:
    """
    Calcula métricas objetivas relacionadas aos combates.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> CombatMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        damage_values = [
            match.total_damage_to_players
            for match in matches
        ]

        eliminated_values = [
            match.players_eliminated
            for match in matches
        ]

        return CombatMetrics(
            average_damage_to_players=round(
                mean(damage_values),
                2,
            ),
            average_players_eliminated=round(
                mean(eliminated_values),
                2,
            ),
        )