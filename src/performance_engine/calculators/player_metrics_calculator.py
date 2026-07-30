from src.performance_engine.models import Match, PlayerMetrics

from .combat_metrics_calculator import CombatMetricsCalculator
from .consistency_metrics_calculator import (
    ConsistencyMetricsCalculator,
)
from .economy_metrics_calculator import EconomyMetricsCalculator
from .general_metrics_calculator import GeneralMetricsCalculator


class PlayerMetricsCalculator:
    """
    Orquestra os calculators e produz o PlayerMetrics completo.

    Não implementa fórmulas próprias. Cada cálculo permanece sob
    responsabilidade de seu calculator específico.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> PlayerMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        return PlayerMetrics(
            general=GeneralMetricsCalculator.calculate(matches),
            consistency=ConsistencyMetricsCalculator.calculate(matches),
            combat=CombatMetricsCalculator.calculate(matches),
            economy=EconomyMetricsCalculator.calculate(matches),
        )