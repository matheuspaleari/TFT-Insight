from src.recommendation_engine.models import (
    CompositionRecommendation,
)
from .confidence import RecommendationConfidenceEngine


class ConfidenceAwareCompositionEngine:
    @classmethod
    def recommend(
        cls,
        *,
        composition_history,
        limit: int = 8,
    ) -> tuple[CompositionRecommendation, ...]:
        results = []

        for profile in composition_history.profiles:
            contest_score = (
                max(0.0, 100.0 - profile.average_contest_score)
                if profile.average_contest_score is not None
                else 50.0
            )

            performance = (
                profile.top4_rate * 0.40
                + profile.win_rate * 0.25
                + (
                    100.0
                    - (profile.average_placement - 1.0)
                    / 7.0
                    * 100.0
                ) * 0.25
                + contest_score * 0.10
            )

            confidence = RecommendationConfidenceEngine.calculate(
                sample_size=profile.matches_played,
                target_sample=20,
            )

            final_score = RecommendationConfidenceEngine.apply(
                performance_score=performance,
                confidence_score=confidence.score,
            )

            if profile.matches_played <= 1:
                final_score = min(final_score, 35.0)
            elif profile.matches_played <= 2:
                final_score = min(final_score, 50.0)
            elif profile.matches_played <= 4:
                final_score = min(final_score, 65.0)

            if confidence.level == "Exploratória":
                label = "Exploratória"
            elif final_score >= 75:
                label = "Consolidada"
            elif final_score >= 60:
                label = "Boa alternativa"
            elif final_score >= 45:
                label = "Promissora"
            else:
                label = "Amostra insuficiente"

            results.append(
                CompositionRecommendation(
                    composition_key=profile.composition_key,
                    carry_character_id=profile.carry_character_id,
                    matches_played=profile.matches_played,
                    average_placement=profile.average_placement,
                    top4_rate=profile.top4_rate,
                    win_rate=profile.win_rate,
                    average_contest_score=profile.average_contest_score,
                    recommendation_score=round(final_score, 2),
                    label=label,
                    explanation=(
                        f"Performance {performance:.1f}/100; "
                        f"confiança {confidence.score:.1f}% "
                        f"({confidence.level})."
                    ),
                    evidence=(
                        f"Partidas: {profile.matches_played}",
                        f"Top 4: {profile.top4_rate:.1f}%",
                        f"Vitória: {profile.win_rate:.1f}%",
                    ),
                )
            )

        return tuple(
            sorted(
                results,
                key=lambda item: (
                    item.recommendation_score,
                    item.matches_played,
                ),
                reverse=True,
            )[:limit]
        )
