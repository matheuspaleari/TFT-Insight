from enum import Enum


class FlexLevel(str, Enum):
    VERY_LOW = "Muito baixa"
    LOW = "Baixa"
    MEDIUM = "Média"
    HIGH = "Alta"
    VERY_HIGH = "Muito alta"

    @classmethod
    def from_score(
        cls,
        score: float,
    ) -> "FlexLevel":
        value = max(0.0, min(float(score), 100.0))

        if value <= 20.0:
            return cls.VERY_LOW
        if value <= 40.0:
            return cls.LOW
        if value <= 60.0:
            return cls.MEDIUM
        if value <= 80.0:
            return cls.HIGH
        return cls.VERY_HIGH
