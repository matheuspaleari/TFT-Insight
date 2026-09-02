"""
Calculadora das métricas objetivas de combate.
"""

from statistics import mean

from src.performance_engine.models import CombatMetrics, Match

from .combat_availability import CombatAvailabilityChecker


class CombatMetricsCalculator:
    """
    Calcula métricas objetivas relacionadas aos combates.

    Quando a fonte retorna dano e eliminações zerados de forma sistêmica,
    as métricas de combate são marcadas como indisponíveis (None) em vez de
    serem interpretadas como desempenho real igual a zero.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> CombatMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        availability = CombatAvailabilityChecker.evaluate(
            matches
        )

        if not availability.available:
            return CombatMetrics(
                average_damage_to_players=None,
                average_players_eliminated=None,
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
