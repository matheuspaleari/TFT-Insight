from src.sprint1_engine.models import PregameGuidanceReport
from .confidence_engine import GlobalConfidenceEngine


class PregameGuidanceEngine:
    @classmethod
    def build(
        cls,
        *,
        carry_contest_rate: float,
        high_contest_rate: float,
        level_8_rate: float,
        level_9_rate: float,
        carry_full_item_rate: float,
        tank_full_item_rate: float,
        sample_size: int,
    ) -> PregameGuidanceReport:
        if carry_contest_rate >= 60 or high_contest_rate >= 35:
            pivot = (
                "Ponto de atenção: não comprometa todos os recursos cedo. "
                "Mantenha uma segunda linha de carry compatível com os itens."
            )
        elif carry_contest_rate >= 45:
            pivot = (
                "Ponto de atenção: monitore o carry antes de fechar a composição; "
                "prepare pivot caso dois adversários disputem a mesma unidade."
            )
        else:
            pivot = (
                "Ponto de atenção: a contestação não é o principal risco; "
                "priorize execução e itemização."
            )

        conditions = []
        if level_9_rate >= 40:
            conditions.append("preservar a opção de chegar ao nível 9")
        elif level_8_rate >= 70:
            conditions.append("estabilizar com consistência no nível 8")
        else:
            conditions.append("proteger economia para alcançar o nível 8")
        if carry_full_item_rate < 70:
            conditions.append("completar três itens no carry")
        if tank_full_item_rate < 70:
            conditions.append("completar a frontline principal")
        win_condition = "Condição de vitória pré-partida: " + "; ".join(conditions) + "."

        confidence = GlobalConfidenceEngine.calculate(
            sample_size=sample_size,
            completeness=1.0,
            agreement=0.85,
            evidence=(
                f"Carry contestado: {carry_contest_rate:.1f}%",
                f"Nível 8: {level_8_rate:.1f}%",
                f"Nível 9: {level_9_rate:.1f}%",
            ),
            limitations=(
                "A orientação é pré-partida e não observa loja, vida ou tabuleiro ao vivo.",
            ),
        )
        return PregameGuidanceReport(
            pivot_attention=pivot,
            win_condition=win_condition,
            confidence=confidence,
            evidence=confidence.evidence,
            limitations=confidence.limitations,
        )
