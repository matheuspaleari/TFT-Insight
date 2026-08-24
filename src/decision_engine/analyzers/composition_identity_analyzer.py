from src.decision_engine.models import CompositionIdentity
from src.performance_engine.models import (
    ParticipantSnapshot,
    TraitSnapshot,
    UnitSnapshot,
)
from src.role_inference.models import ItemClassification
from src.role_inference.services import RoleInferenceEngine


class CompositionIdentityAnalyzer:
    MAX_PRIMARY_TRAITS = 2
    MAX_CORE_UNITS = 5

    IGNORED_TRAIT_EXACT_NAMES = frozenset(
        {
            "TFT17_ResistTank",
            "TFT17_ShieldTank",
            "TFT17_HPTank",
            "TFT17_FlexTrait",
            "TFT17_ManaTrait",
            "TFT17_ASTrait",
            "TFT17_MeleeTrait",
            "TFT17_SummonTrait",
        }
    )

    IGNORED_TRAIT_NAME_PARTS = (
        "UniqueTrait",
        "Role",
    )

    @classmethod
    def analyze(
        cls,
        participant: ParticipantSnapshot,
        *,
        item_classifications: dict[
            str,
            ItemClassification,
        ] | None = None,
    ) -> CompositionIdentity:
        relevant_traits = tuple(
            sorted(
                (
                    trait
                    for trait in participant.active_traits
                    if cls._is_relevant_trait(trait)
                ),
                key=cls._trait_priority,
                reverse=True,
            )
        )

        primary_traits = tuple(
            trait.name
            for trait in relevant_traits[
                :cls.MAX_PRIMARY_TRAITS
            ]
        )

        carry: UnitSnapshot | None = None
        tank: UnitSnapshot | None = None
        support: UnitSnapshot | None = None

        if item_classifications:
            role_report = (
                RoleInferenceEngine.infer_participant(
                    participant=participant,
                    item_classifications=item_classifications,
                )
            )

            carry = cls._find_unit(
                participant,
                (
                    role_report.damage_carry.character_id
                    if role_report.damage_carry
                    else ""
                ),
            )
            tank = cls._find_unit(
                participant,
                (
                    role_report.main_tank.character_id
                    if role_report.main_tank
                    else ""
                ),
            )
            support = cls._find_unit(
                participant,
                (
                    role_report.support.character_id
                    if role_report.support
                    else ""
                ),
            )

        if carry is None:
            carry = cls._legacy_select_carry(participant)

        core_units = cls._select_core_units(
            participant=participant,
            carry=carry,
            tank=tank,
            support=support,
        )

        carry_id = carry.character_id if carry else ""
        tank_id = tank.character_id if tank else ""
        support_id = support.character_id if support else ""

        identity_key = cls._build_identity_key(
            carry_character_id=carry_id,
            tank_character_id=tank_id,
            primary_trait_names=primary_traits,
            core_unit_ids=core_units,
        )

        return CompositionIdentity(
            carry_character_id=carry_id,
            tank_character_id=tank_id,
            support_character_id=support_id,
            primary_trait_names=primary_traits,
            core_unit_ids=core_units,
            identity_key=identity_key,
        )

    @staticmethod
    def _find_unit(
        participant: ParticipantSnapshot,
        character_id: str,
    ) -> UnitSnapshot | None:
        if not character_id:
            return None

        return next(
            (
                unit
                for unit in participant.units
                if unit.character_id == character_id
            ),
            None,
        )

    @staticmethod
    def _legacy_select_carry(
        participant: ParticipantSnapshot,
    ) -> UnitSnapshot | None:
        if not participant.units:
            return None

        itemized = [
            unit
            for unit in participant.units
            if unit.items
        ]

        return max(
            itemized or list(participant.units),
            key=lambda unit: (
                min(len(unit.items), 3),
                unit.rarity,
                unit.tier,
                unit.character_id,
            ),
        )

    @classmethod
    def _select_core_units(
        cls,
        *,
        participant: ParticipantSnapshot,
        carry: UnitSnapshot | None,
        tank: UnitSnapshot | None,
        support: UnitSnapshot | None,
    ) -> tuple[str, ...]:
        priority_units = [
            unit
            for unit in (carry, tank, support)
            if unit is not None
        ]

        ordered = sorted(
            participant.units,
            key=lambda unit: (
                unit in priority_units,
                min(len(unit.items), 3),
                unit.tier,
                unit.rarity,
                unit.character_id,
            ),
            reverse=True,
        )

        selected: list[str] = []

        for unit in [*priority_units, *ordered]:
            if unit.character_id in selected:
                continue

            selected.append(unit.character_id)

            if len(selected) >= cls.MAX_CORE_UNITS:
                break

        return tuple(selected)

    @classmethod
    def _is_relevant_trait(
        cls,
        trait: TraitSnapshot,
    ) -> bool:
        name = trait.name.strip()

        if not name or name in cls.IGNORED_TRAIT_EXACT_NAMES:
            return False

        return not any(
            ignored_part in name
            for ignored_part in cls.IGNORED_TRAIT_NAME_PARTS
        )

    @staticmethod
    def _trait_priority(
        trait: TraitSnapshot,
    ) -> tuple[int, int, int, str]:
        return (
            trait.tier_current,
            trait.style,
            trait.num_units,
            trait.name,
        )

    @staticmethod
    def _build_identity_key(
        *,
        carry_character_id: str,
        tank_character_id: str,
        primary_trait_names: tuple[str, ...],
        core_unit_ids: tuple[str, ...],
    ) -> str:
        traits_part = (
            "+".join(primary_trait_names)
            if primary_trait_names
            else "NO_PRIMARY_TRAIT"
        )

        carry_part = carry_character_id or "NO_CARRY"
        tank_part = tank_character_id or "NO_TANK"
        units_part = (
            "+".join(core_unit_ids)
            if core_unit_ids
            else "NO_CORE_UNITS"
        )

        return (
            f"{traits_part}|{carry_part}|"
            f"{tank_part}|{units_part}"
        )
