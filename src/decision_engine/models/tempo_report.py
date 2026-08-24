from dataclasses import dataclass

from .analysis_availability import (
    AnalysisAvailability,
)


@dataclass(slots=True, frozen=True)
class TempoReport:
    availability: AnalysisAvailability

    score: float
    label: str

    average_last_round: float
    average_time_eliminated: float
    average_players_eliminated: float
    average_damage_to_players: float

    early_exit_rate: float
    late_game_rate: float
    elimination_pressure_rate: float

    matches_analyzed: int
    summary: str
