from statistics import mean

from src.decision_engine.models import (
    AnalysisAvailability,
    EconomyReport,
)
from src.performance_engine.models import Match


class EconomyHistoryAnalyzer:
    """
    Analisa apenas os sinais realmente disponíveis no histórico oficial.

    O histórico não informa cada compra, venda, roll ou momento exato
    de subida de nível. Portanto, este relatório mede resultado econômico
    final, não decisões completas de economia durante a partida.
    """

    @classmethod
    def analyze(
        cls,
        matches: list[Match],
    ) -> EconomyReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        levels = [match.level for match in matches]
        gold = [match.gold_left for match in matches]
        last_rounds = [match.last_round for match in matches]

        level_8_rate = (
            sum(level >= 8 for level in levels)
            / len(levels)
            * 100.0
        )

        level_9_rate = (
            sum(level >= 9 for level in levels)
            / len(levels)
            * 100.0
        )

        low_level_late_rate = (
            sum(
                level <= 7 and last_round >= 30
                for level, last_round
                in zip(levels, last_rounds)
            )
            / len(levels)
            * 100.0
        )

        average_level = mean(levels)
        average_gold = mean(gold)
        average_last_round = mean(last_rounds)

        score = (
            min(average_level / 9.0, 1.0) * 45.0
            + min(level_8_rate / 100.0, 1.0) * 30.0
            + min(level_9_rate / 100.0, 1.0) * 15.0
            + max(
                0.0,
                1.0 - low_level_late_rate / 100.0,
            ) * 10.0
        )

        label = cls._label(score)

        if low_level_late_rate >= 30.0:
            summary = (
                "Há partidas longas terminando em nível baixo. "
                "Isso pode indicar dificuldade para converter "
                "economia em nível ou força de tabuleiro."
            )
        elif level_8_rate >= 70.0:
            summary = (
                "Você chega ao nível 8 com boa frequência. "
                "O resultado final de economia parece consistente."
            )
        else:
            summary = (
                "A progressão de nível é intermediária. "
                "Ainda não há evidência suficiente para afirmar "
                "se o problema é roll, gasto ou perda de vida."
            )

        return EconomyReport(
            availability=AnalysisAvailability.yes(),
            score=round(score, 2),
            label=label,
            average_level=round(average_level, 2),
            average_gold_left=round(average_gold, 2),
            average_last_round=round(
                average_last_round,
                2,
            ),
            level_8_rate=round(level_8_rate, 2),
            level_9_rate=round(level_9_rate, 2),
            low_level_late_rate=round(
                low_level_late_rate,
                2,
            ),
            matches_analyzed=len(matches),
            summary=summary,
        )

    @staticmethod
    def _label(score: float) -> str:
        if score < 35.0:
            return "Fraca"
        if score < 55.0:
            return "Abaixo da média"
        if score < 75.0:
            return "Consistente"
        return "Muito forte"
