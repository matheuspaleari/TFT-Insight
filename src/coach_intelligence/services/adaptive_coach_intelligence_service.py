from __future__ import annotations

from src.coach_intelligence.services.adaptive_coaching_strategy_engine import (
    AdaptiveCoachingStrategyEngine,
)
from src.coach_intelligence.services.adaptive_intelligence_foundation import (
    AdaptiveIntelligenceFoundation,
)
from src.coach_intelligence.services.coach_explanation_engine import (
    CoachExplanationEngine,
)


class AdaptiveCoachIntelligenceService:
    """
    Consolida 11.1-11.6 em payload seguro para API/UI.
    """

    @classmethod
    def build(
        cls,
        *,
        puuid: str,
        assessments,
        pedagogical_memory: dict | None,
        training_history: list[dict],
        priority_skill_id: str,
        current_task_id: str | None,
        player_repository,
        persist_profile: bool = True,
    ) -> dict:
        foundation = (
            AdaptiveIntelligenceFoundation.build(
                puuid=puuid,
                assessments=assessments,
                pedagogical_memory=pedagogical_memory,
                training_history=training_history,
                current_priority_skill_id=priority_skill_id,
                player_repository=player_repository,
                persist=persist_profile,
            )
        )

        strategy = (
            AdaptiveCoachingStrategyEngine.decide(
                foundation=foundation,
                priority_skill_id=priority_skill_id,
                current_task_id=current_task_id,
            )
        )

        explanation = (
            CoachExplanationEngine.explain(
                strategy=strategy,
                foundation=foundation,
            )
        )

        return {
            "strategy": strategy.to_dict(),
            "explanation": explanation.to_dict(),
            "profile": foundation[
                "profile"
            ],
            "evolution": foundation[
                "evolution"
            ],
            "cross_skill_insights": foundation[
                "cross_skill_insights"
            ],
            "training_effectiveness": foundation[
                "training_effectiveness"
            ],
        }
