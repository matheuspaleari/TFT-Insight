from enum import Enum


class MetricType(str, Enum):
    """
    Métricas utilizadas no cálculo de desempenho.
    """

    DAMAGE_TO_PLAYERS = "average_damage_to_players"
    PLAYERS_ELIMINATED = "average_players_eliminated"
    LEVEL = "average_level"
    CONSISTENCY = "placement_standard_deviation"