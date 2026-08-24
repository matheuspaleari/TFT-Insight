from src.sprint1_engine.models import CrossAnalysisReport
from .confidence_engine import GlobalConfidenceEngine


class CrossAnalyzer:
    @classmethod
    def analyze(
        cls,
        *,
        strategic_score: float,
        economy_score: float,
        itemization_score: float,
        tempo_score: float,
        contest_score: float,
        flex_score: float,
        sample_size: int,
    ) -> CrossAnalysisReport:
        interactions, priorities = [], []

        if contest_score < 55 and flex_score < 60:
            interactions.append(
                "Contestação alta combinada com pouca flexibilidade aumenta o risco de insistência."
            )
            priorities.append("Preparar uma composição alternativa antes de comprometer recursos.")
        if itemization_score < 65 and tempo_score < 65:
            interactions.append(
                "Itemização incompleta combinada com tempo baixo sugere estabilização tardia."
            )
            priorities.append("Concentrar itens em carry e tank antes de distribuir recursos.")
        if economy_score >= 75 and tempo_score < 60:
            interactions.append(
                "Economia forte sem conversão em tempo indica possível atraso na estabilização."
            )
            priorities.append("Revisar o momento de gastar ou subir de nível.")
        if strategic_score >= 75 and contest_score < 55:
            interactions.append(
                "Boa execução geral está sendo limitada principalmente pela disputa de unidades."
            )

        score = (
            strategic_score * 0.25
            + economy_score * 0.15
            + itemization_score * 0.20
            + tempo_score * 0.15
            + contest_score * 0.15
            + flex_score * 0.10
        )
        label = "Muito forte" if score >= 80 else "Boa" if score >= 70 else "Regular" if score >= 55 else "Atenção"
        confidence = GlobalConfidenceEngine.calculate(
            sample_size=sample_size,
            completeness=1.0,
            agreement=0.9 if len(interactions) <= 2 else 0.8,
            evidence=(f"{len(interactions)} interações estratégicas detectadas",),
            limitations=("Cruzamentos indicam padrões associados, não causalidade.",),
        )
        return CrossAnalysisReport(
            score=round(score, 2),
            label=label,
            confidence=confidence,
            interactions=tuple(interactions),
            priorities=tuple(priorities),
            evidence=confidence.evidence,
            limitations=confidence.limitations,
        )
