from enum import Enum


class PredictionRisk(str, Enum):
    LOW = "Baixo"
    MEDIUM = "Médio"
    HIGH = "Alto"
    VERY_HIGH = "Muito alto"
