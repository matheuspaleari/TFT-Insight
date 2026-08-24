from enum import Enum


class RecommendationPriority(str, Enum):
    CRITICAL = "Crítica"
    HIGH = "Alta"
    MEDIUM = "Média"
    LOW = "Baixa"
