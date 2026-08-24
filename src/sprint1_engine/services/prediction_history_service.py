from uuid import uuid4

from src.sprint1_engine.models import (
    PredictionHistoryRecord,
    SprintPredictionReport,
)
from src.sprint1_engine.repositories import KnowledgeRepository


class PredictionHistoryService:
    @classmethod
    def save_prediction(
        cls,
        *,
        repository: KnowledgeRepository,
        match_id: str,
        player_puuid: str,
        source: str,
        patch: str,
        set_number: int | None,
        prediction: SprintPredictionReport,
        model_version: str,
    ) -> str:
        prediction_id = str(uuid4())
        repository.save_prediction(
            PredictionHistoryRecord(
                prediction_id=prediction_id,
                match_id=match_id,
                player_puuid=player_puuid,
                source=source,
                patch=patch,
                set_number=set_number,
                top1_probability=prediction.top1_probability,
                top4_probability=prediction.top4_probability,
                bot4_probability=prediction.bot4_probability,
                expected_placement=prediction.expected_placement,
                confidence=prediction.confidence.score,
                model_version=model_version,
            )
        )
        return prediction_id

    @classmethod
    def resolve_prediction(
        cls,
        *,
        repository: KnowledgeRepository,
        match_id: str,
        actual_placement: int,
    ) -> int:
        return repository.resolve_prediction(
            match_id=match_id,
            actual_placement=actual_placement,
        )
