from __future__ import annotations

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
from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogEntry,
    UnitCatalogRepository,
)


class RoleInferenceEngine:
    """
    Inferência de papel V2 para o Set 18.

    Regras principais:
    - o catálogo manual de unidades é a autoridade estrutural;
    - itens refinam força/ranking, mas não criam elegibilidade de papel;
    - estrelas e custo servem apenas como sinais leves de desempate;
    - unidades fora do catálogo permanecem UNKNOWN;
    - nenhum fallback força a existência de um carry.
    """

    MIN_ITEM_CONFIDENCE = 55.0

    # Bases estruturais do catálogo manual.
    CARRY_BASE = 70.0
    TANK_BASE = 70.0
    SUPPORT_BASE = 70.0

    # Bases para unidades explicitamente híbridas.
    HYBRID_CARRY_BASE = 62.0
    HYBRID_TANK_BASE = 60.0
    HYBRID_SUPPORT_BASE = 55.0

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
        catalog_entry = UnitCatalogRepository.get(
            character_id=unit.character_id
        )

        if catalog_entry is None:
            return cls._infer_uncatalogued_unit(
                unit=unit,
                item_classifications=item_classifications,
            )

        return cls._infer_catalog_unit(
            unit=unit,
            entry=catalog_entry,
            item_classifications=item_classifications,
        )

    @classmethod
    def _collect_item_scores(
        cls,
        *,
        unit: UnitSnapshot,
        item_classifications: dict[str, ItemClassification],
    ) -> tuple[float, float, float, float, int, list[str]]:
        offense_total = 0.0
        defense_total = 0.0
        utility_total = 0.0
        confidence_total = 0.0
        considered = 0
        evidence: list[str] = []

        for item_id in unit.items:
            classification = item_classifications.get(item_id)

            if classification is None:
                evidence.append("item sem classificação V2")
                continue

            if classification.confidence < cls.MIN_ITEM_CONFIDENCE:
                evidence.append(
                    "item ignorado por confiança baixa "
                    f"({classification.confidence:.0f}%)"
                )
                continue

            weight = classification.confidence / 100.0

            offense_total += classification.offense_score * weight
            defense_total += classification.defense_score * weight
            utility_total += classification.utility_score * weight
            confidence_total += classification.confidence
            considered += 1

            evidence.append(
                "item: "
                f"{classification.category.value} | "
                f"O={classification.offense_score:.0f} "
                f"D={classification.defense_score:.0f} "
                f"U={classification.utility_score:.0f}"
            )

        if considered == 0:
            return 0.0, 0.0, 0.0, 0.0, 0, evidence

        return (
            offense_total / considered,
            defense_total / considered,
            utility_total / considered,
            confidence_total / considered,
            considered,
            evidence,
        )

    @classmethod
    def _infer_uncatalogued_unit(
        cls,
        *,
        unit: UnitSnapshot,
        item_classifications: dict[str, ItemClassification],
    ) -> UnitRoleAssessment:
        (
            item_offense,
            item_defense,
            item_utility,
            average_item_confidence,
            considered,
            evidence,
        ) = cls._collect_item_scores(
            unit=unit,
            item_classifications=item_classifications,
        )

        evidence.insert(
            0,
            "unit_catalog_v2: unidade não catalogada; papel preservado como UNKNOWN",
        )

        if considered:
            evidence.append(
                "itens observados apenas como evidência; "
                "não podem criar papel para unidade sem catálogo"
            )

        confidence = 0.0
        if considered:
            confidence = min(35.0, average_item_confidence * 0.35)

        return UnitRoleAssessment(
            character_id=unit.character_id,
            role=UnitRole.UNKNOWN,
            confidence=round(confidence, 2),
            offense_score=round(min(item_offense, 55.0), 2),
            defense_score=round(min(item_defense, 55.0), 2),
            utility_score=round(min(item_utility, 55.0), 2),
            item_ids=unit.items,
            evidence=tuple(evidence),
        )

    @classmethod
    def _infer_unit_from_items(
        cls,
        *,
        unit: UnitSnapshot,
        item_classifications: dict[str, ItemClassification],
    ) -> UnitRoleAssessment:
        """
        Compatibilidade com chamadas antigas.

        No V2, itemização sozinha não define mais o papel de uma unidade.
        """
        return cls._infer_uncatalogued_unit(
            unit=unit,
            item_classifications=item_classifications,
        )

    @classmethod
    def _infer_catalog_unit(
        cls,
        *,
        unit: UnitSnapshot,
        entry: UnitCatalogEntry,
        item_classifications: dict[str, ItemClassification],
    ) -> UnitRoleAssessment:
        (
            item_offense,
            item_defense,
            item_utility,
            average_item_confidence,
            considered,
            evidence,
        ) = cls._collect_item_scores(
            unit=unit,
            item_classifications=item_classifications,
        )

        evidence.insert(
            0,
            "unit_catalog_v2: "
            f"{entry.display_name} | {entry.role_label} | "
            f"carry_eligible={entry.carry_eligible}",
        )

        role = cls._catalog_role(entry)

        # Estrelas e custo são sinais leves de desempate.
        # Eles nunca alteram o papel estrutural.
        star_tiebreak = min(max(unit.tier - 1, 0) * 2.0, 4.0)
        cost_tiebreak = min(max(entry.cost - 1, 0) * 0.75, 3.0)

        offense = 0.0
        defense = 0.0
        utility = 0.0

        if role == UnitRole.DAMAGE_CARRY:
            # Item ofensivo ajuda; item defensivo não vira bônus ofensivo.
            offensive_alignment = max(
                0.0,
                item_offense
                - item_defense * 0.50
                - item_utility * 0.20,
            )

            offense = min(
                100.0,
                cls.CARRY_BASE
                + offensive_alignment * 0.25
                + star_tiebreak
                + cost_tiebreak,
            )
            defense = min(60.0, item_defense * 0.55 + star_tiebreak)
            utility = min(60.0, item_utility * 0.55)

        elif role == UnitRole.TANK:
            defensive_alignment = max(
                0.0,
                item_defense
                - item_offense * 0.40
                - item_utility * 0.15,
            )

            offense = min(55.0, item_offense * 0.45)
            defense = min(
                100.0,
                cls.TANK_BASE
                + defensive_alignment * 0.25
                + star_tiebreak
                + cost_tiebreak,
            )
            utility = min(65.0, item_utility * 0.60)

        elif role == UnitRole.SUPPORT:
            utility_alignment = max(
                0.0,
                item_utility
                - item_offense * 0.20
                - item_defense * 0.15,
            )

            offense = min(50.0, item_offense * 0.40)
            defense = min(65.0, item_defense * 0.55)
            utility = min(
                100.0,
                cls.SUPPORT_BASE
                + utility_alignment * 0.25
                + star_tiebreak * 0.50
                + cost_tiebreak,
            )

        elif role == UnitRole.HYBRID:
            role_key = entry.primary_role.casefold()

            carry_base = (
                cls.HYBRID_CARRY_BASE
                if entry.carry_eligible or "carry" in role_key
                else 35.0
            )
            tank_base = (
                cls.HYBRID_TANK_BASE
                if "tank" in role_key or "frontline" in role_key
                else 35.0
            )
            support_base = (
                cls.HYBRID_SUPPORT_BASE
                if "support" in role_key
                else 30.0
            )

            offense = min(
                100.0,
                carry_base
                + item_offense * 0.25
                + (
                    star_tiebreak + cost_tiebreak
                    if entry.carry_eligible
                    else 0.0
                ),
            )
            defense = min(
                100.0,
                tank_base
                + item_defense * 0.25
                + (
                    star_tiebreak + cost_tiebreak
                    if "tank" in role_key or "frontline" in role_key
                    else 0.0
                ),
            )
            utility = min(
                100.0,
                support_base
                + item_utility * 0.25
                + (
                    cost_tiebreak
                    if "support" in role_key
                    else 0.0
                ),
            )

        else:
            # O catálogo marcou explicitamente como unknown.
            offense = min(item_offense, 55.0)
            defense = min(item_defense, 55.0)
            utility = min(item_utility, 55.0)

        confidence = cls._catalog_confidence(
            role=role,
            considered=considered,
            average_item_confidence=average_item_confidence,
        )

        evidence.extend(
            (
                f"display_name: {entry.display_name}",
                f"role manual: {entry.primary_role}",
                f"{considered} itens considerados",
                f"estrelas: {unit.tier}",
                f"custo catálogo: {entry.cost}",
                "papel estrutural não pode ser alterado por itens/estrelas/custo",
            )
        )

        return UnitRoleAssessment(
            character_id=unit.character_id,
            role=role,
            confidence=round(confidence, 2),
            offense_score=round(offense, 2),
            defense_score=round(defense, 2),
            utility_score=round(utility, 2),
            item_ids=unit.items,
            evidence=tuple(evidence),
        )

    @staticmethod
    def _catalog_confidence(
        *,
        role: UnitRole,
        considered: int,
        average_item_confidence: float,
    ) -> float:
        if role == UnitRole.UNKNOWN:
            return 45.0 if considered else 35.0

        if considered == 0:
            return 90.0

        return min(
            100.0,
            90.0
            + average_item_confidence * 0.05
            + min(considered, 3) * 1.5,
        )

    @staticmethod
    def _catalog_role(entry: UnitCatalogEntry) -> UnitRole:
        role = entry.primary_role.casefold()

        if role == "unknown":
            return UnitRole.UNKNOWN

        has_carry = entry.carry_eligible or "carry" in role
        has_tank = "tank" in role or "frontline" in role
        has_support = "support" in role
        explicitly_hybrid = "hybrid" in role

        structural_roles = sum(
            (
                bool(has_carry),
                bool(has_tank),
                bool(has_support),
            )
        )

        if explicitly_hybrid or structural_roles > 1:
            return UnitRole.HYBRID

        if has_carry and entry.carry_eligible:
            return UnitRole.DAMAGE_CARRY

        if has_tank:
            return UnitRole.TANK

        if has_support:
            return UnitRole.SUPPORT

        return UnitRole.UNKNOWN

    @classmethod
    def _assessment_eligible_for_role(
        cls,
        *,
        assessment: UnitRoleAssessment,
        role: UnitRole,
    ) -> bool:
        if assessment.role == role:
            return True

        # Híbridos mantêm o papel HYBRID no assessment, mas podem competir
        # nas rotas explicitamente permitidas pelo catálogo manual.
        if assessment.role != UnitRole.HYBRID:
            return False

        entry = UnitCatalogRepository.get(
            character_id=assessment.character_id
        )
        if entry is None:
            return False

        role_key = entry.primary_role.casefold()

        if role == UnitRole.DAMAGE_CARRY:
            return entry.carry_eligible

        if role == UnitRole.TANK:
            return "tank" in role_key or "frontline" in role_key

        if role == UnitRole.SUPPORT:
            return "support" in role_key

        return False

    @classmethod
    def _select_main_role(
        cls,
        *,
        assessments: tuple[UnitRoleAssessment, ...],
        role: UnitRole,
        score_name: str,
    ) -> UnitRoleAssessment | None:
        candidates = [
            assessment
            for assessment in assessments
            if cls._assessment_eligible_for_role(
                assessment=assessment,
                role=role,
            )
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
