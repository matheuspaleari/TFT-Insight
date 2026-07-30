from statistics import mean

from src.performance_engine.models import EconomyMetrics, Match


class EconomyMetricsCalculator:
    """
    Calcula métricas econômicas diretamente observáveis.

    Ouro restante não representa, isoladamente, boa ou má economia.
    """

    @staticmethod
    def calculate(matches: list[Match]) -> EconomyMetrics:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        gold_values = [
            match.gold_left
            for match in matches
        ]

        return EconomyMetrics(
            average_gold_left=round(
                mean(gold_values),
                2,
            ),
        )