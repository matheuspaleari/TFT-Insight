"""
Analisador histórico de contestação.
"""

from collections import Counter
from statistics import mean

from src.decision_engine.models import (
    ContestHistoryReport,
    ContestLevel,
    ContestReport,
)
from src.performance_engine.models import Match

from .contest_analyzer import ContestAnalyzer


class ContestHistoryAnalyzer:
    """
    Consolida a análise individual de várias partidas.

    A ordem recebida é preservada. Portanto, a primeira partida da lista
    deve ser a mais recente para que latest_report represente corretamente
    a última partida do jogador.
    """

    HIGH_CONTEST_THRESHOLD = 60.0

    @classmethod
    def analyze(
        cls,
        matches: list[Match],
    ) -> ContestHistoryReport:
        """
        Analisa várias partidas e produz uma visão geral.
        """

        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        reports_with_placement = tuple(
            (
                ContestAnalyzer.analyze(match),
                match.placement,
            )
            for match in matches
        )

        reports = tuple(
            report
            for report, _
            in reports_with_placement
        )

        scores = [
            report.score
            for report in reports
        ]

        placements = [
            placement
            for _, placement
            in reports_with_placement
        ]

        contested_placements = [
            placement
            for report, placement
            in reports_with_placement
            if (
                report.score
                > cls.HIGH_CONTEST_THRESHOLD
            )
        ]

        uncontested_placements = [
            placement
            for report, placement
            in reports_with_placement
            if (
                report.score
                <= cls.HIGH_CONTEST_THRESHOLD
            )
        ]

        high_contest_matches = sum(
            1
            for report in reports
            if (
                report.score
                > cls.HIGH_CONTEST_THRESHOLD
            )
        )

        carry_contested_matches = sum(
            1
            for report in reports
            if report.carry_contested
        )

        unit_counter = Counter(
            unit_id
            for report in reports
            for unit_id in report.contested_unit_ids
        )

        trait_counter = Counter(
            trait_name
            for report in reports
            for trait_name
            in report.contested_trait_names
        )

        average_score = round(
            mean(scores),
            2,
        )

        return ContestHistoryReport(
            matches_analyzed=len(reports),
            average_score=average_score,
            highest_score=round(
                max(scores),
                2,
            ),
            level=ContestLevel.from_score(
                average_score
            ),
            high_contest_rate=round(
                high_contest_matches
                / len(reports)
                * 100.0,
                2,
            ),
            carry_contest_rate=round(
                carry_contested_matches
                / len(reports)
                * 100.0,
                2,
            ),
            average_placement=round(
                mean(placements),
                2,
            ),
            contested_average_placement=(
                round(
                    mean(contested_placements),
                    2,
                )
                if contested_placements
                else None
            ),
            uncontested_average_placement=(
                round(
                    mean(uncontested_placements),
                    2,
                )
                if uncontested_placements
                else None
            ),
            most_contested_unit_id=(
                unit_counter.most_common(1)[0][0]
                if unit_counter
                else ""
            ),
            most_contested_trait_name=(
                trait_counter.most_common(1)[0][0]
                if trait_counter
                else ""
            ),
            latest_report=reports[0],
            match_reports=reports,
        )
