from __future__ import annotations

from src.coaching_engine import (
    ConfidenceAwareCompositionEngine,
    RecommendationConfidenceEngine,
)
from src.decision_engine.analyzers.composition_cluster_analyzer import (
    CompositionClusterAnalyzer,
)
from src.decision_engine.models import CompositionHistoryReport

from src.composition_intelligence_v2.models.composition_intelligence import (
    CompositionIntelligenceProfile,
    CompositionIntelligenceReport,
)


class CompositionIntelligenceV2:
    """
    Enriquecimento seguro sobre o Composition Engine já existente.

    Não reconstrói decisões durante a partida.
    Não afirma intenção de forçar composição.
    Não trata uma amostra de 1-2 jogos como prova de melhor composição.
    """

    MIN_RELIABLE_SAMPLE = 3

    @classmethod
    def build(
        cls,
        history: CompositionHistoryReport,
    ) -> CompositionIntelligenceReport:
        clusters = CompositionClusterAnalyzer.cluster(
            history.snapshots
        )

        cluster_by_id = {
            cluster.cluster_id: cluster
            for cluster in clusters
        }

        confidence_recommendations = {
            item.composition_key: item
            for item in ConfidenceAwareCompositionEngine.recommend(
                composition_history=history,
                limit=max(len(history.profiles), 1),
            )
        }

        enriched = []

        for profile in history.profiles:
            cluster = cluster_by_id.get(
                profile.composition_key
            )

            if cluster is None:
                raise ValueError(
                    "Não foi possível relacionar CompositionProfile "
                    f"ao cluster {profile.composition_key}."
                )

            representative = cluster.representative

            confidence = RecommendationConfidenceEngine.calculate(
                sample_size=profile.matches_played,
                target_sample=20,
            )

            recommendation = confidence_recommendations.get(
                profile.composition_key
            )

            enriched.append(
                CompositionIntelligenceProfile(
                    composition_key=profile.composition_key,
                    carry_character_id=representative.carry_character_id,
                    tank_character_id=representative.tank_character_id,
                    support_character_id=representative.support_character_id,
                    primary_trait_names=representative.trait_names,
                    core_unit_ids=representative.unit_ids,
                    matches_played=profile.matches_played,
                    usage_rate=profile.usage_rate,
                    average_placement=profile.average_placement,
                    top4_rate=profile.top4_rate,
                    win_rate=profile.win_rate,
                    average_contest_score=profile.average_contest_score,
                    confidence_score=confidence.score,
                    confidence_level=confidence.level,
                    recommendation_score=(
                        recommendation.recommendation_score
                        if recommendation is not None
                        else 0.0
                    ),
                    recommendation_label=(
                        recommendation.label
                        if recommendation is not None
                        else confidence.level
                    ),
                    sample_is_reliable=(
                        profile.matches_played
                        >= cls.MIN_RELIABLE_SAMPLE
                    ),
                )
            )

        profiles = tuple(
            sorted(
                enriched,
                key=lambda item: (
                    item.matches_played,
                    item.recommendation_score,
                    -item.average_placement,
                ),
                reverse=True,
            )
        )

        most_used = max(
            profiles,
            key=lambda item: (
                item.matches_played,
                -item.average_placement,
            ),
        )

        supported = [
            item
            for item in profiles
            if item.sample_is_reliable
        ]

        best_supported = (
            min(
                supported,
                key=lambda item: (
                    item.average_placement,
                    -item.top4_rate,
                    -item.matches_played,
                ),
            )
            if supported
            else None
        )

        repetition_signal, repetition_interpretation = (
            cls._repetition_semantics(
                history.repetition_rate
            )
        )

        return CompositionIntelligenceReport(
            matches_analyzed=history.matches_analyzed,
            unique_compositions=history.unique_compositions,
            diversity_rate=history.diversity_rate,
            repetition_rate=history.repetition_rate,
            repetition_signal=repetition_signal,
            repetition_interpretation=repetition_interpretation,
            most_used=most_used,
            best_supported=best_supported,
            profiles=profiles,
            limitations=(
                "A composição representa o board final observado; "
                "não reconstrói todas as transições da partida.",
                "Carry e tank são inferências baseadas nos sinais "
                "disponíveis e podem ter confiança limitada.",
                "Melhor desempenho histórico não significa que a composição "
                "era a melhor escolha para um lobby específico.",
            ),
        )

    @staticmethod
    def _repetition_semantics(
        repetition_rate: float,
    ) -> tuple[str, str]:
        if repetition_rate >= 50.0:
            return (
                "ALTA_REPETICAO",
                "Você termina muitas partidas com estruturas semelhantes. "
                "Isso mostra repetição no histórico, não prova que você "
                "entrou na partida decidido a forçar uma composição.",
            )

        if repetition_rate >= 25.0:
            return (
                "REPETICAO_MODERADA",
                "Algumas estruturas aparecem com frequência, mas o histórico "
                "ainda apresenta variedade relevante.",
            )

        return (
            "ALTA_DIVERSIDADE",
            "Nenhuma estrutura domina fortemente o histórico recente.",
        )
