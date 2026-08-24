from src.decision_engine.models import (
    CompositionHistoryReport,
)

from src.recommendation_engine.models import (
    CompositionRecommendation,
)


class CompositionRecommendationEngine:
    MIN_MATCHES = 2

    @classmethod
    def recommend(
        cls,
        *,
        composition_history: CompositionHistoryReport,
        limit: int = 5,
    ) -> tuple[CompositionRecommendation, ...]:
        recommendations = []

        for profile in composition_history.profiles:
            sample_factor = min(
                profile.matches_played / 10.0,
                1.0,
            )

            contest_component = (
                max(
                    0.0,
                    100.0 - profile.average_contest_score,
                )
                if profile.average_contest_score is not None
                else 50.0
            )

            score = (
                profile.top4_rate * 0.40
                + profile.win_rate * 0.25
                + (
                    100.0
                    - (profile.average_placement - 1.0)
                    / 7.0
                    * 100.0
                ) * 0.20
                + contest_component * 0.10
                + sample_factor * 100.0 * 0.05
            )

            if profile.matches_played < cls.MIN_MATCHES:
                label = "Exploratória"
                explanation = (
                    "O resultado é promissor, mas a amostra ainda "
                    "é pequena."
                )
            elif score >= 75.0:
                label = "Priorizar"
                explanation = (
                    "A composição combina bom resultado, Top 4 e "
                    "controle de contestação."
                )
            elif score >= 60.0:
                label = "Boa alternativa"
                explanation = (
                    "A composição apresenta desempenho consistente."
                )
            else:
                label = "Situacional"
                explanation = (
                    "Use apenas quando itens e lobby favorecerem."
                )

            recommendations.append(
                CompositionRecommendation(
                    composition_key=profile.composition_key,
                    carry_character_id=profile.carry_character_id,
                    matches_played=profile.matches_played,
                    average_placement=profile.average_placement,
                    top4_rate=profile.top4_rate,
                    win_rate=profile.win_rate,
                    average_contest_score=(
                        profile.average_contest_score
                    ),
                    recommendation_score=round(score, 2),
                    label=label,
                    explanation=explanation,
                    evidence=(
                        (
                            "Partidas: "
                            f"{profile.matches_played}"
                        ),
                        (
                            "Colocação média: "
                            f"{profile.average_placement:.2f}"
                        ),
                        f"Top 4: {profile.top4_rate:.1f}%",
                        f"Vitória: {profile.win_rate:.1f}%",
                    ),
                )
            )

        return tuple(
            sorted(
                recommendations,
                key=lambda item: (
                    item.recommendation_score,
                    item.matches_played,
                ),
                reverse=True,
            )[:limit]
        )
