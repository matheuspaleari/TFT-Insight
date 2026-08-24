"""
Serviço responsável por executar e persistir
a decisão pedagógica do Learning Engine.
"""

from src.learning.models import LearningRecommendation
from src.learning.services.learning_engine import LearningEngine
from src.learning.services.skill_mapping_service import (
    SkillMappingService,
)
from src.performance_engine.models import Performance
from src.storage import PlayerRepository


class PlayerLearningService:
    """
    Coordena o fluxo completo de aprendizagem do jogador.

    Fluxo:

        Performance
            ↓
        Skill Mapping
            ↓
        Learning Engine
            ↓
        Learning Recommendation
            ↓
        PlayerRepository
    """

    def __init__(
        self,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.player_repository = (
            player_repository
            or PlayerRepository()
        )

    def evaluate(
        self,
        *,
        puuid: str,
        benchmark_id: str,
        match_ids: list[str],
        performance: Performance,
    ) -> LearningRecommendation:
        """
        Avalia o jogador e salva a recomendação atual.
        """

        assessments = SkillMappingService.assess(
            performance=performance,
        )

        recommendation = LearningEngine.recommend(
            assessments=assessments,
        )

        learning_path = (
            self.player_repository.save_learning_recommendation(
                puuid=puuid,
                benchmark_id=benchmark_id,
                match_ids=match_ids,
                recommendation_data=(
                    recommendation.to_dict()
                ),
            )
        )

        print(
            "Recomendação de aprendizado persistida em: "
            f"{learning_path}"
        )

        return recommendation