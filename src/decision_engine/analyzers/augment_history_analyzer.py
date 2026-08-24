from collections import Counter

from src.decision_engine.models import (
    AnalysisAvailability,
    AugmentReport,
)
from src.performance_engine.models import Match


class AugmentHistoryAnalyzer:
    @classmethod
    def analyze(
        cls,
        matches: list[Match],
    ) -> AugmentReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        names = []

        for match in matches:
            participant = match.analyzed_participant

            if participant is None:
                continue

            names.extend(
                augment.name
                for augment in participant.augments
                if augment.name
            )

        if not names:
            return AugmentReport(
                availability=AnalysisAvailability.no(
                    "Os augments não estão presentes "
                    "nos dados transformados deste set."
                ),
                augments_detected=0,
                unique_augments=0,
                summary=(
                    "O módulo foi preparado, mas não fará "
                    "inferências sem dados reais de augments."
                ),
            )

        counter = Counter(names)
        most_common_name, most_common_count = (
            counter.most_common(1)[0]
        )

        return AugmentReport(
            availability=AnalysisAvailability.yes(),
            augments_detected=len(names),
            unique_augments=len(counter),
            summary=(
                f"Augment mais frequente: "
                f"{most_common_name} "
                f"({most_common_count} usos). "
                "A avaliação de qualidade será adicionada "
                "quando houver benchmark por augment."
            ),
        )
