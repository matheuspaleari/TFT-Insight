from math import exp

from src.sprint1_engine.models import AnalysisConfidence


class GlobalConfidenceEngine:
    @classmethod
    def calculate(
        cls,
        *,
        sample_size: int,
        completeness: float = 1.0,
        agreement: float = 1.0,
        target_sample: int = 50,
        evidence: tuple[str, ...] = (),
        limitations: tuple[str, ...] = (),
    ) -> AnalysisConfidence:
        completeness = max(0.0, min(completeness, 1.0))
        agreement = max(0.0, min(agreement, 1.0))
        sample_component = 1.0 - exp(-2.0 * sample_size / target_sample)
        score = 100.0 * (
            sample_component * 0.55
            + completeness * 0.25
            + agreement * 0.20
        )
        if score >= 85:
            level = "Muito alta"
        elif score >= 70:
            level = "Alta"
        elif score >= 50:
            level = "Moderada"
        elif score >= 30:
            level = "Baixa"
        else:
            level = "Muito baixa"
        return AnalysisConfidence(
            score=round(score, 2),
            level=level,
            sample_size=sample_size,
            evidence=evidence,
            limitations=limitations,
        )
