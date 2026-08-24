from src.decision_engine.models import (
    AnalysisAvailability,
    ItemizationReport,
)
from src.performance_engine.models import Match
from src.role_inference.models import (
    ItemClassification,
    UnitRole,
)
from src.role_inference.services import (
    RoleInferenceEngine,
)


class ItemizationHistoryAnalyzer:
    """
    Mede como os itens finais foram distribuídos entre papéis.

    Esta análise não avalia componentes temporários nem o momento em que
    cada item foi feito. Ela usa apenas o tabuleiro final preservado.
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
    ) -> ItemizationReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        if not item_classifications:
            return ItemizationReport(
                availability=AnalysisAvailability.no(
                    "Classificações de itens não foram fornecidas."
                ),
                score=0.0,
                label="Indisponível",
                carry_item_share=0.0,
                tank_item_share=0.0,
                support_item_share=0.0,
                unknown_item_share=0.0,
                carry_full_item_rate=0.0,
                tank_full_item_rate=0.0,
                matches_analyzed=len(matches),
                summary=(
                    "Execute primeiro o benchmark Challenger "
                    "de classificação de itens."
                ),
            )

        role_item_counts = {
            UnitRole.DAMAGE_CARRY: 0,
            UnitRole.TANK: 0,
            UnitRole.SUPPORT: 0,
        }

        unknown_items = 0
        total_items = 0
        carry_full_matches = 0
        tank_full_matches = 0

        for match in matches:
            participant = match.analyzed_participant

            if participant is None:
                continue

            report = RoleInferenceEngine.infer_participant(
                participant=participant,
                item_classifications=item_classifications,
            )

            for assessment in report.assessments:
                item_count = len(assessment.item_ids)
                total_items += item_count

                if assessment.role in role_item_counts:
                    role_item_counts[
                        assessment.role
                    ] += item_count
                else:
                    unknown_items += item_count

            if (
                report.damage_carry is not None
                and len(
                    report.damage_carry.item_ids
                ) >= 3
            ):
                carry_full_matches += 1

            if (
                report.main_tank is not None
                and len(
                    report.main_tank.item_ids
                ) >= 3
            ):
                tank_full_matches += 1

        if total_items == 0:
            return ItemizationReport(
                availability=AnalysisAvailability.no(
                    "Nenhum item final foi encontrado nas partidas."
                ),
                score=0.0,
                label="Indisponível",
                carry_item_share=0.0,
                tank_item_share=0.0,
                support_item_share=0.0,
                unknown_item_share=100.0,
                carry_full_item_rate=0.0,
                tank_full_item_rate=0.0,
                matches_analyzed=len(matches),
                summary=(
                    "As partidas não possuem itemização final "
                    "suficiente para análise."
                ),
            )

        carry_share = (
            role_item_counts[
                UnitRole.DAMAGE_CARRY
            ]
            / total_items
            * 100.0
        )
        tank_share = (
            role_item_counts[
                UnitRole.TANK
            ]
            / total_items
            * 100.0
        )
        support_share = (
            role_item_counts[
                UnitRole.SUPPORT
            ]
            / total_items
            * 100.0
        )
        unknown_share = (
            unknown_items
            / total_items
            * 100.0
        )

        carry_full_rate = (
            carry_full_matches
            / len(matches)
            * 100.0
        )
        tank_full_rate = (
            tank_full_matches
            / len(matches)
            * 100.0
        )

        score = (
            min(carry_full_rate / 100.0, 1.0) * 40.0
            + min(tank_full_rate / 100.0, 1.0) * 30.0
            + max(
                0.0,
                1.0 - unknown_share / 100.0,
            ) * 20.0
            + min(
                (carry_share + tank_share)
                / 70.0,
                1.0,
            ) * 10.0
        )

        label = cls._label(score)

        if unknown_share >= 35.0:
            summary = (
                "Muitos itens ficaram em unidades sem papel claro. "
                "Pode haver distribuição híbrida ou papéis ainda "
                "não reconhecidos pelo modelo."
            )
        elif carry_full_rate >= 70.0 and tank_full_rate >= 60.0:
            summary = (
                "Carry e tank recebem conjuntos completos "
                "com boa frequência."
            )
        else:
            summary = (
                "A distribuição de itens é razoável, mas nem sempre "
                "carry e tank terminam com três itens."
            )

        return ItemizationReport(
            availability=AnalysisAvailability.yes(),
            score=round(score, 2),
            label=label,
            carry_item_share=round(carry_share, 2),
            tank_item_share=round(tank_share, 2),
            support_item_share=round(
                support_share,
                2,
            ),
            unknown_item_share=round(
                unknown_share,
                2,
            ),
            carry_full_item_rate=round(
                carry_full_rate,
                2,
            ),
            tank_full_item_rate=round(
                tank_full_rate,
                2,
            ),
            matches_analyzed=len(matches),
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
        return "Muito boa"
