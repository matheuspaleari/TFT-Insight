from __future__ import annotations

from math import exp, log10
from time import perf_counter
from uuid import uuid4

from src.integration_engine.config import (
    IntegrationSettings,
)
from src.integration_engine.contracts import (
    AnalyzeRequest,
    AnalyzeResponse,
    ApiMeta,
    CoachResult,
    EvidenceItem,
    FeatureContribution,
    LimitationItem,
    PredictionResult,
    RecommendationItem,
)


class InsightEngine:
    """
    Facade pública da TFT Insight Engine.

    Esta classe é o ponto único de entrada para API, SDK e parceiros.
    Os contratos públicos não expõem as classes internas dos analyzers.
    """

    FEATURE_WEIGHTS = {
        "economy": 0.18,
        "itemization": 0.24,
        "tempo": 0.16,
        "contest": 0.18,
        "flex": 0.10,
        "benchmark": 0.14,
    }

    def __init__(
        self,
        settings: IntegrationSettings | None = None,
    ) -> None:
        self.settings = (
            settings
            or IntegrationSettings.from_environment()
        )

    def analyze(
        self,
        request: AnalyzeRequest,
    ) -> AnalyzeResponse:
        started = perf_counter()

        signals = request.signals

        values = {
            "economy": signals.economy_score,
            "itemization": signals.itemization_score,
            "tempo": signals.tempo_score,
            "contest": signals.contest_score,
            "flex": signals.flex_score,
            "benchmark": signals.benchmark_score,
        }

        contributions = tuple(
            self._contribution(
                feature=feature,
                score=values[feature],
                weight=weight,
            )
            for feature, weight
            in self.FEATURE_WEIGHTS.items()
        )

        overall_score = sum(
            item.contribution
            for item in contributions
        )

        prediction = self._prediction(
            overall_score=overall_score,
            sample_size=signals.sample_size,
            average_placement=(
                signals.average_placement
            ),
        )

        recommendations = self._recommendations(
            request=request,
        )

        coach = self._coach(
            request=request,
            recommendations=recommendations,
        )

        elapsed_ms = (
            perf_counter() - started
        ) * 1000.0

        request_id = (
            request.request_id
            or str(uuid4())
        )

        evidence = tuple(
            EvidenceItem(
                key=item.feature,
                value=f"{item.score:.2f}",
                description=(
                    f"Peso público: "
                    f"{item.weight:.0%}; "
                    f"contribuição: "
                    f"{item.contribution:.2f}"
                ),
            )
            for item in contributions
        )

        limitations = (
            LimitationItem(
                code="historical_state",
                message=(
                    "A análise usa sinais históricos ou "
                    "pré-calculados e não reconstrói "
                    "cada decisão por rodada."
                ),
            ),
            LimitationItem(
                code="non_causal",
                message=(
                    "Recomendações representam associação "
                    "estatística, não causalidade comprovada."
                ),
            ),
            LimitationItem(
                code="calibration_scope",
                message=(
                    "Probabilidades devem ser calibradas "
                    "por patch, set e população."
                ),
            ),
        )

        return AnalyzeResponse(
            meta=ApiMeta(
                request_id=request_id,
                api_version=self.settings.api_version,
                contract_version=(
                    self.settings.contract_version
                ),
                processing_ms=round(
                    elapsed_ms,
                    3,
                ),
            ),
            overall_score=round(
                overall_score,
                2,
            ),
            classification=self._classification(
                overall_score
            ),
            prediction=prediction,
            feature_importance=tuple(
                sorted(
                    contributions,
                    key=lambda item: abs(
                        item.contribution - 50.0 * item.weight
                    ),
                    reverse=True,
                )
            ),
            recommendations=recommendations,
            coach=coach,
            evidence=evidence,
            limitations=limitations,
        )

    @staticmethod
    def _contribution(
        *,
        feature: str,
        score: float,
        weight: float,
    ) -> FeatureContribution:
        direction = (
            "positive"
            if score >= 70.0
            else (
                "negative"
                if score < 55.0
                else "neutral"
            )
        )

        return FeatureContribution(
            feature=feature,
            score=round(score, 2),
            weight=weight,
            contribution=round(
                score * weight,
                2,
            ),
            direction=direction,
        )

    @classmethod
    def _prediction(
        cls,
        *,
        overall_score: float,
        sample_size: int,
        average_placement: float | None,
    ) -> PredictionResult:
        top4_probability = (
            100.0
            / (
                1.0
                + exp(
                    -0.065
                    * (overall_score - 55.0)
                )
            )
        )

        top1_probability = (
            100.0
            / (
                1.0
                + exp(
                    -0.055
                    * (overall_score - 72.0)
                )
            )
        ) * 0.42

        bot4_probability = (
            100.0 - top4_probability
        )

        score_placement = (
            8.0
            - overall_score / 100.0 * 7.0
        )

        expected_placement = (
            score_placement
            if average_placement is None
            else (
                score_placement * 0.55
                + average_placement * 0.45
            )
        )

        expected_placement = max(
            1.0,
            min(expected_placement, 8.0),
        )

        confidence = min(
            100.0,
            45.0
            + log10(sample_size + 1)
            / log10(101)
            * 55.0,
        )

        risk_score = (
            bot4_probability * 0.60
            + (100.0 - overall_score)
            * 0.40
        )

        if risk_score < 25.0:
            risk = "Baixo"
        elif risk_score < 45.0:
            risk = "Médio"
        elif risk_score < 65.0:
            risk = "Alto"
        else:
            risk = "Muito alto"

        return PredictionResult(
            top1_probability=round(
                top1_probability,
                2,
            ),
            top4_probability=round(
                top4_probability,
                2,
            ),
            bot4_probability=round(
                bot4_probability,
                2,
            ),
            expected_placement=round(
                expected_placement,
                2,
            ),
            risk=risk,
            confidence=round(
                confidence,
                2,
            ),
        )

    @classmethod
    def _recommendations(
        cls,
        *,
        request: AnalyzeRequest,
    ) -> tuple[RecommendationItem, ...]:
        signals = request.signals

        factors = [
            (
                "Itemização",
                signals.itemization_score,
                (
                    "Complete carry e tank antes de "
                    "espalhar itens em unidades secundárias."
                ),
            ),
            (
                "Contestação",
                signals.contest_score,
                (
                    "Monitore o carry antes de "
                    "comprometer recursos; prepare pivot "
                    "com dois adversários na mesma unidade."
                ),
            ),
            (
                "Economia",
                signals.economy_score,
                (
                    "Ajuste o timing entre estabilizar "
                    "e preservar recursos para subir de nível."
                ),
            ),
            (
                "Tempo",
                signals.tempo_score,
                (
                    "Fortaleça o tabuleiro intermediário "
                    "para chegar ao late game com mais vida."
                ),
            ),
            (
                "Flexibilidade",
                signals.flex_score,
                (
                    "Mantenha uma segunda linha de carry "
                    "compatível com seus componentes."
                ),
            ),
        ]

        recommendations = []

        for category, score, action in sorted(
            factors,
            key=lambda item: item[1],
        ):
            if score >= 80.0:
                continue

            gap = 100.0 - score

            if score < 40.0:
                priority = "critical"
            elif score < 55.0:
                priority = "high"
            elif score < 70.0:
                priority = "medium"
            else:
                priority = "low"

            recommendations.append(
                RecommendationItem(
                    priority=priority,
                    category=category,
                    title=(
                        f"Melhorar {category.lower()}"
                    ),
                    action=action,
                    confidence=round(
                        min(
                            95.0,
                            60.0
                            + gap * 0.35
                            + min(
                                signals.sample_size,
                                50,
                            ) * 0.25,
                        ),
                        2,
                    ),
                )
            )

        return tuple(
            recommendations[:4]
        )

    @staticmethod
    def _coach(
        *,
        request: AnalyzeRequest,
        recommendations: tuple[
            RecommendationItem,
            ...,
        ],
    ) -> CoachResult:
        signals = request.signals

        if (
            signals.carry_contested
            or signals.opponents_on_carry >= 2
        ):
            attention = (
                "O carry está sob contestação direta. "
                "Defina previamente uma composição alternativa."
            )
        elif signals.contest_score < 60.0:
            attention = (
                "A sobreposição com o lobby merece atenção. "
                "Evite fechar a composição cedo."
            )
        else:
            attention = (
                "A contestação não é o principal risco. "
                "Priorize execução e conversão de recursos."
            )

        if signals.itemization_score >= 75.0:
            win_condition = (
                "Preservar a opção de chegar ao nível 9 "
                "e completar carry e tank."
            )
        else:
            win_condition = (
                "Completar primeiro o conjunto do carry "
                "e garantir uma frontline funcional."
            )

        primary = (
            recommendations[0]
            if recommendations
            else None
        )

        if primary is None:
            headline = (
                "Execução consistente sem prioridade crítica."
            )
            summary = (
                "Mantenha o padrão atual e aumente "
                "a amostra para validar o comportamento."
            )
        else:
            headline = (
                f"Prioridade principal: "
                f"{primary.category}"
            )
            summary = primary.action

        return CoachResult(
            headline=headline,
            summary=summary,
            pregame_attention=attention,
            win_condition=win_condition,
        )

    @staticmethod
    def _classification(
        score: float,
    ) -> str:
        if score < 40.0:
            return "Crítica"
        if score < 55.0:
            return "Atenção"
        if score < 70.0:
            return "Regular"
        if score < 80.0:
            return "Boa"
        return "Muito forte"
