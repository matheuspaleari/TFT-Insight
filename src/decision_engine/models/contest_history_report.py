"""
Relatório histórico de contestação do jogador.
"""

from dataclasses import dataclass, field

from .contest_level import ContestLevel
from .contest_report import ContestReport


@dataclass(slots=True, frozen=True)
class ContestHistoryReport:
    """
    Consolida a contestação observada em várias partidas.

    Mantém a última partida separada da visão geral para que
    Dashboard, Inspector e Coach possam apresentar ambos os contextos.
    """

    matches_analyzed: int

    average_score: float
    highest_score: float
    level: ContestLevel

    high_contest_rate: float
    carry_contest_rate: float

    average_placement: float
    contested_average_placement: float | None
    uncontested_average_placement: float | None

    most_contested_unit_id: str = ""
    most_contested_trait_name: str = ""

    latest_report: ContestReport | None = None

    match_reports: tuple[
        ContestReport,
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if self.matches_analyzed < 1:
            raise ValueError(
                "ContestHistoryReport.matches_analyzed "
                "deve ser maior que zero."
            )

        if (
            self.matches_analyzed
            != len(self.match_reports)
        ):
            raise ValueError(
                "matches_analyzed deve corresponder "
                "à quantidade de match_reports."
            )

        if self.latest_report is None:
            raise ValueError(
                "ContestHistoryReport.latest_report "
                "deve ser informado."
            )

        if (
            not self.match_reports
            or self.match_reports[0].match_id
            != self.latest_report.match_id
        ):
            raise ValueError(
                "latest_report deve corresponder "
                "ao primeiro relatório do histórico."
            )

        for field_name, value in (
            ("average_score", self.average_score),
            ("highest_score", self.highest_score),
            ("high_contest_rate", self.high_contest_rate),
            ("carry_contest_rate", self.carry_contest_rate),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )

        self._validate_placement(
            "average_placement",
            self.average_placement,
        )

        if self.contested_average_placement is not None:
            self._validate_placement(
                "contested_average_placement",
                self.contested_average_placement,
            )

        if self.uncontested_average_placement is not None:
            self._validate_placement(
                "uncontested_average_placement",
                self.uncontested_average_placement,
            )

    @property
    def high_contest_matches(self) -> int:
        """
        Retorna quantas partidas tiveram contestação alta ou extrema.
        """

        return sum(
            1
            for report in self.match_reports
            if report.score > 60.0
        )

    @property
    def carry_contested_matches(self) -> int:
        """
        Retorna quantas partidas tiveram o carry contestado.
        """

        return sum(
            1
            for report in self.match_reports
            if report.carry_contested
        )

    @property
    def placement_impact(self) -> float | None:
        """
        Diferença observada de colocação entre partidas contestadas
        e não contestadas.

        Valor positivo indica colocação média pior quando contestado.
        """

        if (
            self.contested_average_placement is None
            or self.uncontested_average_placement is None
        ):
            return None

        return round(
            self.contested_average_placement
            - self.uncontested_average_placement,
            2,
        )

    @staticmethod
    def _validate_placement(
        field_name: str,
        value: float,
    ) -> None:
        if not 1.0 <= value <= 8.0:
            raise ValueError(
                f"{field_name} deve estar entre 1 e 8."
            )
