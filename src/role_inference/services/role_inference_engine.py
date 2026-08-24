from src.performance_engine.models import (
    ParticipantSnapshot,
    UnitSnapshot,
)
from src.role_inference.models import (
    ItemClassification,
    ParticipantRoleReport,
    UnitRole,
    UnitRoleAssessment,
)


class RoleInferenceEngine:
    """
    Identifica carry, tank e suporte sem listas manuais de campeões.

    O motor usa as classificações aprendidas no benchmark Challenger,
    além de itemização, estrelas e raridade da unidade.
    """

    MIN_ITEM_CONFIDENCE = 55.0
    MIN_ROLE_SCORE = 24.0
    MIN_ROLE_MARGIN = 7.0

    @classmethod
    def infer_participant(
        cls,
        *,
        participant: ParticipantSnapshot,
        item_classifications: dict[str, ItemClassification],
    ) -> ParticipantRoleReport:
        assessments = tuple(
            cls.infer_unit(
                unit=unit,
                item_classifications=item_classifications,
            )
            for unit in participant.units
        )

        return ParticipantRoleReport(
            participant_puuid=participant.puuid,
            damage_carry=cls._select_main_role(
                assessments=assessments,
                role=UnitRole.DAMAGE_CARRY,
                score_name="offense_score",
            ),
            main_tank=cls._select_main_role(
                assessments=assessments,
                role=UnitRole.TANK,
                score_name="defense_score",
            ),
            support=cls._select_main_role(
                assessments=assessments,
                role=UnitRole.SUPPORT,
                score_name="utility_score",
            ),
            assessments=assessments,
        )

    @classmethod
    def infer_unit(
        cls,
        *,
        unit: UnitSnapshot,
        item_classifications: dict[str, ItemClassification],
    ) -> UnitRoleAssessment:
        totals = {
            "offense": 0.0,
            "defense": 0.0,
            "utility": 0.0,
        }
        confidence_total = 0.0
        considered = 0
        evidence: list[str] = []

        for item_id in unit.items:
            classification = item_classifications.get(item_id)

            if classification is None:
                evidence.append(
                    f"{item_id}: sem classificação"
                )
                continue

            if classification.confidence < cls.MIN_ITEM_CONFIDENCE:
                evidence.append(
                    f"{item_id}: confiança baixa "
                    f"({classification.confidence:.0f}%)"
                )
                continue

            weight = classification.confidence / 100.0
            totals["offense"] += (
                classification.offense_score * weight
            )
            totals["defense"] += (
                classification.defense_score * weight
            )
            totals["utility"] += (
                classification.utility_score * weight
            )
            confidence_total += classification.confidence
            considered += 1

            evidence.append(
                f"{item_id}: {classification.category.value} "
                f"({classification.confidence:.0f}%)"
            )

        if considered == 0:
            return UnitRoleAssessment(
                character_id=unit.character_id,
                role=UnitRole.UNKNOWN,
                confidence=0.0,
                offense_score=0.0,
                defense_score=0.0,
                utility_score=0.0,
                item_ids=unit.items,
                evidence=tuple(evidence),
            )

        offense = totals["offense"] / considered
        defense = totals["defense"] / considered
        utility = totals["utility"] / considered

        item_bonus = min(considered, 3) * 4.0
        star_bonus = max(unit.tier - 1, 0) * 2.5
        rarity_bonus = min(unit.rarity, 5) * 1.2

        offense = min(
            100.0,
            offense + item_bonus + star_bonus + rarity_bonus,
        )
        defense = min(
            100.0,
            defense
            + item_bonus
            + star_bonus * 1.4
            + rarity_bonus * 0.8,
        )
        utility = min(
            100.0,
            utility
            + item_bonus * 0.8
            + star_bonus * 0.5
            + rarity_bonus,
        )

        role_scores = {
            UnitRole.DAMAGE_CARRY: offense,
            UnitRole.TANK: defense,
            UnitRole.SUPPORT: utility,
        }

        ordered = sorted(
            role_scores.values(),
            reverse=True,
        )
        dominant = ordered[0]
        margin = dominant - ordered[1]
        role = max(role_scores, key=role_scores.get)

        if dominant < cls.MIN_ROLE_SCORE:
            role = UnitRole.UNKNOWN
        elif margin < cls.MIN_ROLE_MARGIN:
            role = UnitRole.HYBRID

        average_item_confidence = confidence_total / considered
        sample_factor = min(considered / 3.0, 1.0)

        confidence = (
            average_item_confidence * 0.55
            + min(margin * 2.0, 100.0) * 0.30
            + sample_factor * 100.0 * 0.15
        )

        if role == UnitRole.UNKNOWN:
            confidence = min(confidence, 45.0)
        elif role == UnitRole.HYBRID:
            confidence = min(confidence, 70.0)

        evidence.extend(
            (
                f"{considered} itens considerados",
                f"estrelas: {unit.tier}",
                f"raridade: {unit.rarity}",
                f"margem do papel: {margin:.1f}",
            )
        )

        return UnitRoleAssessment(
            character_id=unit.character_id,
            role=role,
            confidence=round(min(confidence, 100.0), 2),
            offense_score=round(offense, 2),
            defense_score=round(defense, 2),
            utility_score=round(utility, 2),
            item_ids=unit.items,
            evidence=tuple(evidence),
        )

    @staticmethod
    def _select_main_role(
        *,
        assessments: tuple[UnitRoleAssessment, ...],
        role: UnitRole,
        score_name: str,
    ) -> UnitRoleAssessment | None:
        candidates = [
            assessment
            for assessment in assessments
            if assessment.role == role
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda assessment: (
                getattr(assessment, score_name),
                assessment.confidence,
                len(assessment.item_ids),
                assessment.character_id,
            ),
        )
