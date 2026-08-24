from __future__ import annotations

from math import exp
from statistics import mean

from src.decision_engine.models import (
    ContestHistoryReport,
    FlexReport,
    MatchPredictionReport,
    PredictionRisk,
    StrategicReport,
)
from src.performance_engine.models import Match


class PredictionEngine:
    """
    Prediction Engine v1 baseado em regras calibradas.

    Esta versão NÃO é um modelo de machine learning treinado.
    Ela estima Top 4, vitória e colocação esperada combinando:

    - histórico real do jogador;
    - execução estratégica;
    - contestação;
    - flexibilidade;
    - tamanho da amostra.

    O objetivo é criar uma baseline explicável para posterior comparação
    com um modelo estatístico treinado em partidas Challenger.
    """

    @classmethod
    def predict(
        cls,
        *,
        history_matches: list[Match],
        strategic_report: StrategicReport,
        contest_history: ContestHistoryReport | None = None,
        flex_report: FlexReport | None = None,
    ) -> MatchPredictionReport:
        if not history_matches:
            raise ValueError(
                "history_matches não pode ser vazio."
            )

        total = len(history_matches)

        historical_top4 = (
            sum(
                match.placement <= 4
                for match in history_matches
            )
            / total
            * 100.0
        )

        historical_win = (
            sum(
                match.placement == 1
                for match in history_matches
            )
            / total
            * 100.0
        )

        average_placement = mean(
            match.placement
            for match in history_matches
        )

        strategic = strategic_report.overall_score
        contest_score = (
            max(
                0.0,
                100.0 - contest_history.average_score,
            )
            if contest_history is not None
            else 50.0
        )
        flex_score = (
            flex_report.score
            if flex_report is not None
            else 50.0
        )

        top4_signal = (
            historical_top4 * 0.45
            + strategic * 0.30
            + contest_score * 0.15
            + flex_score * 0.10
        )

        top4_probability = cls._calibrate_probability(
            top4_signal,
            midpoint=55.0,
            steepness=0.055,
        )

        win_signal = (
            historical_win * 0.45
            + strategic * 0.25
            + contest_score * 0.20
            + flex_score * 0.10
        )

        win_probability = cls._calibrate_probability(
            win_signal,
            midpoint=57.0,
            steepness=0.050,
        ) * 0.55

        expected_placement = (
            average_placement * 0.50
            + cls._score_to_placement(strategic) * 0.25
            + cls._score_to_placement(contest_score) * 0.15
            + cls._score_to_placement(flex_score) * 0.10
        )

        expected_placement = max(
            1.0,
            min(expected_placement, 8.0),
        )

        confidence = cls._confidence(
            sample_size=total,
            modules_available=(
                3
                + int(contest_history is not None)
                + int(flex_report is not None)
            ),
        )

        risk_signals = []
        positive_signals = []

        if strategic >= 75.0:
            positive_signals.append(
                "Execução estratégica histórica forte."
            )
        elif strategic < 55.0:
            risk_signals.append(
                "Execução estratégica histórica irregular."
            )

        if contest_score >= 70.0:
            positive_signals.append(
                "Contestação média controlada."
            )
        elif contest_score < 50.0:
            risk_signals.append(
                "Contestação média elevada."
            )

        if flex_score >= 70.0:
            positive_signals.append(
                "Boa capacidade de adaptação."
            )
        elif flex_score < 50.0:
            risk_signals.append(
                "Baixa flexibilidade recente."
            )

        if historical_top4 >= 60.0:
            positive_signals.append(
                "Taxa histórica de Top 4 acima de 60%."
            )
        elif historical_top4 < 40.0:
            risk_signals.append(
                "Taxa histórica de Top 4 abaixo de 40%."
            )

        risk = cls._risk(
            top4_probability=top4_probability,
            contest_score=contest_score,
            strategic_score=strategic,
        )

        summary = (
            f"Baseline estimada: {top4_probability:.1f}% de Top 4, "
            f"{win_probability:.1f}% de vitória e colocação esperada "
            f"{expected_placement:.2f}. A confiança da previsão é "
            f"{confidence:.1f}%."
        )

        return MatchPredictionReport(
            top4_probability=round(
                top4_probability,
                2,
            ),
            win_probability=round(
                win_probability,
                2,
            ),
            expected_placement=round(
                expected_placement,
                2,
            ),
            risk=risk,
            confidence=round(confidence, 2),
            positive_signals=tuple(positive_signals),
            risk_signals=tuple(risk_signals),
            caveats=(
                (
                    "Esta é uma baseline explicável baseada em regras, "
                    "não um modelo de machine learning treinado."
                ),
                (
                    "A previsão representa o padrão histórico atual e "
                    "não conhece o estado de uma partida futura."
                ),
                (
                    "Probabilidades precisam ser calibradas futuramente "
                    "com uma base rotulada de partidas Challenger."
                ),
            ),
            summary=summary,
        )

    @staticmethod
    def _calibrate_probability(
        signal: float,
        *,
        midpoint: float,
        steepness: float,
    ) -> float:
        return (
            100.0
            / (
                1.0
                + exp(
                    -steepness
                    * (signal - midpoint)
                )
            )
        )

    @staticmethod
    def _score_to_placement(
        score: float,
    ) -> float:
        return (
            8.0
            - max(0.0, min(score, 100.0))
            / 100.0
            * 7.0
        )

    @staticmethod
    def _confidence(
        *,
        sample_size: int,
        modules_available: int,
    ) -> float:
        sample_score = min(
            sample_size / 50.0,
            1.0,
        ) * 70.0

        module_score = min(
            modules_available / 5.0,
            1.0,
        ) * 30.0

        return sample_score + module_score

    @staticmethod
    def _risk(
        *,
        top4_probability: float,
        contest_score: float,
        strategic_score: float,
    ) -> PredictionRisk:
        risk_score = (
            (100.0 - top4_probability) * 0.50
            + (100.0 - contest_score) * 0.25
            + (100.0 - strategic_score) * 0.25
        )

        if risk_score < 25.0:
            return PredictionRisk.LOW
        if risk_score < 45.0:
            return PredictionRisk.MEDIUM
        if risk_score < 65.0:
            return PredictionRisk.HIGH
        return PredictionRisk.VERY_HIGH
