from __future__ import annotations

from src.integration_engine.contracts import (
    AnalysisSignals,
)


class InternalReportAdapter:
    """
    Converte relatórios internos existentes para o contrato público.

    O adapter usa apenas atributos já consolidados e mantém a API
    desacoplada das classes internas da Engine.
    """

    @staticmethod
    def from_reports(
        *,
        strategic_report,
        contest_history,
        flex_report,
        benchmark_score: float = 50.0,
        sample_size: int = 20,
    ) -> AnalysisSignals:
        return AnalysisSignals(
            economy_score=float(
                strategic_report.economy.score
            ),
            itemization_score=float(
                strategic_report.itemization.score
            ),
            tempo_score=float(
                strategic_report.tempo.score
            ),
            contest_score=max(
                0.0,
                100.0
                - float(
                    contest_history.average_score
                ),
            ),
            flex_score=float(
                flex_report.score
            ),
            benchmark_score=float(
                benchmark_score
            ),
            sample_size=sample_size,
            average_placement=float(
                contest_history.average_placement
            ),
        )
