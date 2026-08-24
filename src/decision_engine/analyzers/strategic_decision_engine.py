from src.decision_engine.models import (
    StrategicReport,
)
from src.performance_engine.models import Match
from src.role_inference.models import (
    ItemClassification,
)

from .augment_history_analyzer import (
    AugmentHistoryAnalyzer,
)
from .economy_history_analyzer import (
    EconomyHistoryAnalyzer,
)
from .itemization_history_analyzer import (
    ItemizationHistoryAnalyzer,
)
from .positioning_analyzer import (
    PositioningAnalyzer,
)
from .tempo_history_analyzer import (
    TempoHistoryAnalyzer,
)


class StrategicDecisionEngine:
    """
    Consolida os primeiros módulos estratégicos da Fase 2.
    """

    @classmethod
    def analyze(
        cls,
        matches: list[Match],
        *,
        item_classifications: dict[
            str,
            ItemClassification,
        ],
    ) -> StrategicReport:
        economy = EconomyHistoryAnalyzer.analyze(
            matches
        )
        itemization = (
            ItemizationHistoryAnalyzer.analyze(
                matches,
                item_classifications=(
                    item_classifications
                ),
            )
        )
        tempo = TempoHistoryAnalyzer.analyze(
            matches
        )
        augment = AugmentHistoryAnalyzer.analyze(
            matches
        )
        positioning = PositioningAnalyzer.analyze()

        available_scores = [
            report.score
            for report in (
                economy,
                itemization,
                tempo,
            )
            if report.availability.available
        ]

        overall_score = (
            sum(available_scores)
            / len(available_scores)
            if available_scores
            else 0.0
        )

        ranked = sorted(
            (
                ("Economia", economy.score),
                ("Itemização", itemization.score),
                ("Tempo", tempo.score),
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )

        strengths = tuple(
            f"{name}: {score:.0f}/100"
            for name, score in ranked[:2]
            if score >= 55.0
        )

        priorities = tuple(
            f"{name}: {score:.0f}/100"
            for name, score in reversed(
                ranked[-2:]
            )
            if score < 65.0
        )

        label = cls._label(overall_score)

        summary = (
            f"Execução estratégica geral: {label} "
            f"({overall_score:.1f}/100). "
            "A nota considera apenas módulos suportados "
            "pelos dados atuais."
        )

        return StrategicReport(
            overall_score=round(
                overall_score,
                2,
            ),
            label=label,
            economy=economy,
            itemization=itemization,
            tempo=tempo,
            augment=augment,
            positioning=positioning,
            strengths=strengths,
            priorities=priorities,
            summary=summary,
        )

    @staticmethod
    def _label(score: float) -> str:
        if score < 35.0:
            return "Fraca"
        if score < 55.0:
            return "Irregular"
        if score < 75.0:
            return "Boa"
        return "Muito forte"
