from dataclasses import dataclass
from math import exp


@dataclass(slots=True, frozen=True)
class RecommendationConfidence:
    score: float
    level: str
    sample_size: int


class RecommendationConfidenceEngine:
    @classmethod
    def calculate(
        cls,
        *,
        sample_size: int,
        target_sample: int = 20,
    ) -> RecommendationConfidence:
        if sample_size < 0:
            raise ValueError("sample_size inválido.")

        score = (
            0.0
            if sample_size == 0
            else 100.0 * (1.0 - exp(-2.2 * sample_size / target_sample))
        )

        if sample_size <= 1:
            level = "Exploratória"
        elif sample_size <= 3:
            level = "Baixa"
        elif sample_size <= 7:
            level = "Moderada"
        elif sample_size <= 14:
            level = "Boa"
        else:
            level = "Alta"

        return RecommendationConfidence(
            score=round(min(score, 100.0), 2),
            level=level,
            sample_size=sample_size,
        )

    @staticmethod
    def apply(
        *,
        performance_score: float,
        confidence_score: float,
    ) -> float:
        return round(
            performance_score * confidence_score / 100.0,
            2,
        )
