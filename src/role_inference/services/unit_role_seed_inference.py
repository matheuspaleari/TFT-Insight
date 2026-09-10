from src.performance_engine.models import UnitSnapshot
from src.role_inference.models import (
    ItemClassification,
    RoleSeedAssessment,
    UnitRoleSeed,
)
from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogEntry,
    UnitCatalogRepository,
)


class UnitRoleSeedInference:
    """
    Inferência inicial de papel com prioridade para o Unit Catalog V2.

    Ordem:
    1. catálogo manual aprovado do Set 18;
    2. itens classificados, somente se a unidade não estiver catalogada.

    Isso elimina o bootstrap circular para unidades conhecidas:
    os itens deixam de decidir quem o campeão "é" e passam a ser
    evidência complementar/refinamento posterior.
    """

    MIN_ITEM_CONFIDENCE = 55.0

    CATALOG_CONFIDENCE = 95.0
    UNKNOWN_CATALOG_CONFIDENCE = 35.0

    @classmethod
    def infer(
        cls,
        *,
        unit: UnitSnapshot,
        classifications: dict[str, ItemClassification],
    ) -> RoleSeedAssessment:
        catalog_entry = UnitCatalogRepository.get(
            character_id=unit.character_id
        )

        if catalog_entry is not None:
            return cls._from_catalog(
                entry=catalog_entry
            )

        return cls._from_items(
            unit=unit,
            classifications=classifications,
        )

    @classmethod
    def _from_catalog(
        cls,
        *,
        entry: UnitCatalogEntry,
    ) -> RoleSeedAssessment:
        role = cls._catalog_role_to_seed(
            entry=entry
        )

        if role == UnitRoleSeed.DAMAGE_CARRY:
            offense = 95.0
            defense = 10.0
            utility = 10.0
            confidence = cls.CATALOG_CONFIDENCE

        elif role == UnitRoleSeed.TANK:
            offense = 10.0
            defense = 95.0
            utility = 20.0
            confidence = cls.CATALOG_CONFIDENCE

        elif role == UnitRoleSeed.SUPPORT:
            offense = 15.0
            defense = 20.0
            utility = 95.0
            confidence = cls.CATALOG_CONFIDENCE

        else:
            offense = 0.0
            defense = 0.0
            utility = 0.0
            confidence = cls.UNKNOWN_CATALOG_CONFIDENCE

        return RoleSeedAssessment(
            role=role,
            confidence=confidence,
            offense_score=offense,
            defense_score=defense,
            utility_score=utility,
            evidence=(
                "unit_catalog_v2: "
                f"{entry.display_name} | "
                f"{entry.role_label} | "
                f"carry_eligible={entry.carry_eligible}",
            ),
        )

    @staticmethod
    def _catalog_role_to_seed(
        *,
        entry: UnitCatalogEntry,
    ) -> UnitRoleSeed:
        role = entry.primary_role.casefold()

        if role == "unknown":
            return UnitRoleSeed.UNKNOWN

        if entry.carry_eligible:
            return UnitRoleSeed.DAMAGE_CARRY

        if (
            "tank" in role
            or "frontline" in role
        ):
            return UnitRoleSeed.TANK

        if "support" in role:
            return UnitRoleSeed.SUPPORT

        return UnitRoleSeed.UNKNOWN

    @classmethod
    def _from_items(
        cls,
        *,
        unit: UnitSnapshot,
        classifications: dict[str, ItemClassification],
    ) -> RoleSeedAssessment:
        offense = 0.0
        defense = 0.0
        utility = 0.0
        considered = 0
        evidence: list[str] = []

        for item_id in unit.items:
            classification = classifications.get(
                item_id
            )

            if (
                classification is None
                or classification.confidence
                < cls.MIN_ITEM_CONFIDENCE
            ):
                continue

            considered += 1

            offense += (
                classification.offense_score
            )
            defense += (
                classification.defense_score
            )
            utility += (
                classification.utility_score
            )

            evidence.append(
                f"{item_id}: "
                f"{classification.category.value} "
                f"({classification.confidence:.0f}%)"
            )

        if considered == 0:
            return RoleSeedAssessment(
                role=UnitRoleSeed.UNKNOWN,
                confidence=0.0,
                offense_score=0.0,
                defense_score=0.0,
                utility_score=0.0,
                evidence=(
                    "unidade fora do catálogo e nenhum item "
                    "com confiança suficiente",
                ),
            )

        offense /= considered
        defense /= considered
        utility /= considered

        scores = {
            UnitRoleSeed.DAMAGE_CARRY: offense,
            UnitRoleSeed.TANK: defense,
            UnitRoleSeed.SUPPORT: utility,
        }

        ordered = sorted(
            scores.values(),
            reverse=True,
        )

        role = max(
            scores,
            key=scores.get,
        )

        margin = (
            ordered[0] - ordered[1]
            if len(ordered) > 1
            else ordered[0]
        )

        confidence = min(
            100.0,
            45.0
            + considered * 12.0
            + margin * 0.35,
        )

        if (
            ordered[0] < 25.0
            or margin < 8.0
        ):
            role = UnitRoleSeed.UNKNOWN
            confidence = min(
                confidence,
                49.0,
            )

        return RoleSeedAssessment(
            role=role,
            confidence=round(
                confidence,
                2,
            ),
            offense_score=round(
                offense,
                2,
            ),
            defense_score=round(
                defense,
                2,
            ),
            utility_score=round(
                utility,
                2,
            ),
            evidence=tuple(
                evidence
            ),
        )
