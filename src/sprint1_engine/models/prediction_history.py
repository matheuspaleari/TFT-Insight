from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PredictionHistoryRecord:
    prediction_id: str
    match_id: str
    player_puuid: str
    source: str
    patch: str
    set_number: int | None
    top1_probability: float
    top4_probability: float
    bot4_probability: float
    expected_placement: float
    confidence: float
    model_version: str
    actual_placement: int | None = None
