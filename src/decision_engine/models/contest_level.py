"""
Níveis de contestação da composição.
"""

from enum import Enum


class ContestLevel(str, Enum):
    VERY_LOW = "Muito baixa"
    LOW = "Baixa"
    MEDIUM = "Média"
    HIGH = "Alta"
    EXTREME = "Extrema"

    @classmethod
    def from_score(
        cls,
        score: float,
    ) -> "ContestLevel":
        """
        Converte um score entre 0 e 100 em uma classificação.
        """

        normalized_score = max(
            0.0,
            min(float(score), 100.0),
        )

        if normalized_score <= 20.0:
            return cls.VERY_LOW

        if normalized_score <= 40.0:
            return cls.LOW

        if normalized_score <= 60.0:
            return cls.MEDIUM

        if normalized_score <= 80.0:
            return cls.HIGH

        return cls.EXTREME
