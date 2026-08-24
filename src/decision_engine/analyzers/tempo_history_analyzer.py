from statistics import mean

from src.decision_engine.models import (
    AnalysisAvailability,
    TempoReport,
)
from src.performance_engine.models import Match


class TempoHistoryAnalyzer:
    """
    Mede pressão e sobrevivência usando os campos finais da partida.

    Não reconstrói cada estágio nem identifica exatamente o momento
    de spike. Para isso seria necessário um histórico por rodada.
    """

    EARLY_EXIT_ROUND = 24
    LATE_GAME_ROUND = 32

    @classmethod
    def analyze(
        cls,
        matches: list[Match],
    ) -> TempoReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        last_rounds = [
            match.last_round
            for match in matches
        ]
        times = [
            match.time_eliminated
            for match in matches
        ]
        eliminations = [
            match.players_eliminated
            for match in matches
        ]
        damage = [
            match.total_damage_to_players
            for match in matches
        ]

        early_exit_rate = (
            sum(
                last_round <= cls.EARLY_EXIT_ROUND
                for last_round in last_rounds
            )
            / len(matches)
            * 100.0
        )

        late_game_rate = (
            sum(
                last_round >= cls.LATE_GAME_ROUND
                for last_round in last_rounds
            )
            / len(matches)
            * 100.0
        )

        elimination_pressure_rate = (
            sum(
                eliminated >= 1
                for eliminated in eliminations
            )
            / len(matches)
            * 100.0
        )

        average_last_round = mean(last_rounds)
        average_time = mean(times)
        average_eliminations = mean(
            eliminations
        )
        average_damage = mean(damage)

        score = (
            min(
                average_last_round / 38.0,
                1.0,
            ) * 35.0
            + min(
                late_game_rate / 100.0,
                1.0,
            ) * 25.0
            + min(
                average_damage / 120.0,
                1.0,
            ) * 25.0
            + min(
                elimination_pressure_rate
                / 100.0,
                1.0,
            ) * 15.0
        )

        if early_exit_rate >= 35.0:
            summary = (
                "Há muitas eliminações antes do fim do mid game. "
                "O jogador pode estar demorando para estabilizar."
            )
        elif late_game_rate >= 60.0:
            summary = (
                "Você chega ao late game com boa frequência "
                "e mantém pressão razoável sobre o lobby."
            )
        else:
            summary = (
                "O padrão de tempo é intermediário. "
                "Há espaço para melhorar a transição até o late game."
            )

        return TempoReport(
            availability=AnalysisAvailability.yes(),
            score=round(score, 2),
            label=cls._label(score),
            average_last_round=round(
                average_last_round,
                2,
            ),
            average_time_eliminated=round(
                average_time,
                2,
            ),
            average_players_eliminated=round(
                average_eliminations,
                2,
            ),
            average_damage_to_players=round(
                average_damage,
                2,
            ),
            early_exit_rate=round(
                early_exit_rate,
                2,
            ),
            late_game_rate=round(
                late_game_rate,
                2,
            ),
            elimination_pressure_rate=round(
                elimination_pressure_rate,
                2,
            ),
            matches_analyzed=len(matches),
            summary=summary,
        )

    @staticmethod
    def _label(score: float) -> str:
        if score < 35.0:
            return "Lento"
        if score < 55.0:
            return "Instável"
        if score < 75.0:
            return "Consistente"
        return "Muito forte"
