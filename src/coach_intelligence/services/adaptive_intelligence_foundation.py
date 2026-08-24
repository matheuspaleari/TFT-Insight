from __future__ import annotations

from src.coach_intelligence.services.cross_skill_relationship_engine import (
    CrossSkillRelationshipEngine,
)
from src.coach_intelligence.services.player_learning_profile_repository import (
    PlayerLearningProfileRepository,
)
from src.coach_intelligence.services.player_learning_profile_service import (
    PlayerLearningProfileService,
)
from src.coach_intelligence.services.skill_evolution_engine import (
    SkillEvolutionEngine,
)
from src.coach_intelligence.services.training_effectiveness_engine import (
    TrainingEffectivenessEngine,
)


class AdaptiveIntelligenceFoundation:
    """
    Fases 11.1 a 11.4 em uma única leitura.

    Ainda não altera prioridade, missão ou Learning Loop.
    """

    @classmethod
    def build(
        cls,
        *,
        puuid: str,
        assessments,
        pedagogical_memory: dict | None,
        training_history: list[dict],
        current_priority_skill_id: str | None,
        player_repository,
        persist: bool = True,
    ) -> dict:
        repository = (
            PlayerLearningProfileRepository(
                player_repository=(
                    player_repository
                )
            )
        )

        previous = repository.load(
            puuid=puuid
        )

        profile = (
            PlayerLearningProfileService.build(
                assessments=assessments,
                pedagogical_memory=(
                    pedagogical_memory
                ),
                current_priority_skill_id=(
                    current_priority_skill_id
                ),
            )
        )

        evolution = (
            SkillEvolutionEngine.compare(
                current_profile=profile,
                previous_profile=previous,
            )
        )

        cross_skill = (
            CrossSkillRelationshipEngine.analyze(
                profile=profile
            )
        )

        effectiveness = (
            TrainingEffectivenessEngine.evaluate(
                training_history=(
                    training_history
                )
            )
        )

        result = {
            "profile": profile.to_dict(),
            "evolution": [
                item.to_dict()
                for item in evolution
            ],
            "cross_skill_insights": [
                item.to_dict()
                for item in cross_skill
            ],
            "training_effectiveness": [
                item.to_dict()
                for item in effectiveness
            ],
        }

        if persist:
            repository.save(
                puuid=puuid,
                profile=profile.to_dict(),
            )

        return result
