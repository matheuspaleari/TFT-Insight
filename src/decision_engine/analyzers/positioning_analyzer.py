from src.decision_engine.models import (
    AnalysisAvailability,
    PositioningReport,
)


class PositioningAnalyzer:
    @classmethod
    def analyze(cls) -> PositioningReport:
        return PositioningReport(
            availability=AnalysisAvailability.no(
                "A API de histórico não fornece coordenadas "
                "finais das unidades no tabuleiro."
            ),
            summary=(
                "O Positioning Analyzer não inventará uma avaliação. "
                "Ele será ativado quando o projeto capturar posições "
                "por outra fonte confiável ou por leitura do cliente."
            ),
        )
