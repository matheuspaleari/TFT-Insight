from enum import Enum


class ExplanationImpact(str, Enum):
    POSITIVE = "Positivo"
    NEGATIVE = "Negativo"
    NEUTRAL = "Neutro"
    UNAVAILABLE = "Indisponível"
