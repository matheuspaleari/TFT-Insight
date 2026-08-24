from math import exp
from statistics import mean

from src.performance_engine.models import Match
from src.sprint1_engine.models import SprintPredictionReport
from src.sprint1_engine.repositories import KnowledgeRepository
from .confidence_engine import GlobalConfidenceEngine


class SprintPredictionEngine:
    @classmethod
    def predict(
        cls,
        *,
        history_matches: list[Match],
        strategic_score: float,
        contest_score: float,
        flex_score: float,
        knowledge_repository: KnowledgeRepository | None = None,
        patch: str | None = None,
        set_number: int | None = None,
    ) -> SprintPredictionReport:
        if not history_matches:
            raise ValueError("history_matches não pode ser vazio.")

        total = len(history_matches)
        own_top4 = sum(m.placement <= 4 for m in history_matches) / total * 100
        own_win = sum(m.placement == 1 for m in history_matches) / total * 100
        own_average = mean(m.placement for m in history_matches)

        benchmark = {}
        if knowledge_repository is not None:
            benchmark = knowledge_repository.aggregate_source(
                source="challenger", patch=patch, set_number=set_number
            )

        challenger_top4 = benchmark.get("top4_rate", 50.0)
        challenger_win = benchmark.get("win_rate", 12.5)
        challenger_average = benchmark.get("average_placement", 4.5)

        top4_signal = (
            own_top4 * 0.35
            + challenger_top4 * 0.15
            + strategic_score * 0.25
            + contest_score * 0.15
            + flex_score * 0.10
        )
        top4 = cls._logistic(top4_signal, midpoint=56.0, steepness=0.06)

        top1_signal = (
            own_win * 0.35
            + challenger_win * 0.20
            + strategic_score * 0.20
            + contest_score * 0.15
            + flex_score * 0.10
        )
        top1 = cls._logistic(top1_signal, midpoint=33.0, steepness=0.055) * 0.42
        bot4 = 100.0 - top4

        expected = (
            own_average * 0.45
            + challenger_average * 0.15
            + cls._score_to_placement(strategic_score) * 0.20
            + cls._score_to_placement(contest_score) * 0.12
            + cls._score_to_placement(flex_score) * 0.08
        )
        expected = max(1.0, min(expected, 8.0))

        positive, risks = [], []
        if strategic_score >= 75:
            positive.append("Execução estratégica histórica forte.")
        elif strategic_score < 55:
            risks.append("Execução estratégica abaixo do ideal.")
        if contest_score >= 70:
            positive.append("Contestação média controlada.")
        elif contest_score < 50:
            risks.append("Contestação média elevada.")
        if flex_score >= 70:
            positive.append("Boa capacidade de adaptação.")
        elif flex_score < 50:
            risks.append("Flexibilidade recente baixa.")
        if own_top4 >= challenger_top4:
            positive.append("Top 4 pessoal igual ou superior ao benchmark.")
        else:
            risks.append("Top 4 pessoal abaixo do benchmark Challenger.")

        completeness = 1.0 if benchmark else 0.75
        agreement = 1.0 - min(abs(own_top4 - challenger_top4) / 100.0, 0.5)
        confidence = GlobalConfidenceEngine.calculate(
            sample_size=total + int(benchmark.get("sample_size", 0)),
            completeness=completeness,
            agreement=agreement,
            target_sample=200,
            evidence=(
                f"Histórico pessoal: {total} partidas",
                f"Benchmark: {int(benchmark.get('sample_size', 0))} partidas",
            ),
            limitations=(
                "Previsão pré-partida baseada em histórico, não no estado ao vivo.",
            ),
        )

        risk_score = (100 - top4) * 0.55 + (100 - contest_score) * 0.25 + (100 - strategic_score) * 0.20
        risk = "Baixo" if risk_score < 30 else "Médio" if risk_score < 50 else "Alto" if risk_score < 70 else "Muito alto"

        return SprintPredictionReport(
            top1_probability=round(top1, 2),
            top4_probability=round(top4, 2),
            bot4_probability=round(bot4, 2),
            expected_placement=round(expected, 2),
            risk=risk,
            confidence=confidence,
            positive_signals=tuple(positive),
            risk_signals=tuple(risks),
            evidence=(
                f"Top 4 pessoal: {own_top4:.1f}%",
                f"Top 4 Challenger: {challenger_top4:.1f}%",
                f"Score estratégico: {strategic_score:.1f}",
                f"Score de contestação: {contest_score:.1f}",
                f"Score de flexibilidade: {flex_score:.1f}",
            ),
            limitations=(
                "Probabilidades são uma baseline explicável e ainda precisam de calibração supervisionada.",
                "Pivot e win condition são dicas pré-partida, não decisões em tempo real.",
            ),
        )

    @staticmethod
    def _logistic(signal: float, *, midpoint: float, steepness: float) -> float:
        return 100.0 / (1.0 + exp(-steepness * (signal - midpoint)))

    @staticmethod
    def _score_to_placement(score: float) -> float:
        return 8.0 - max(0.0, min(score, 100.0)) / 100.0 * 7.0
