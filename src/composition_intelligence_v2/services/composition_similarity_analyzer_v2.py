from __future__ import annotations

from src.decision_engine.models import CompositionSnapshot

from src.composition_intelligence_v2.models.composition_similarity_v2 import (
    CompositionSimilarityV2Result,
)


class CompositionSimilarityAnalyzerV2:
    """
    Similaridade estrutural de composição V2.

    Mudanças em relação à V1:
    - carry: 35%
    - tank: 10%
    - traits: 30%
    - core units: 25%
    - Support NÃO participa do score.
    - trait igual sozinho não pode carregar um par com carry diferente
      e baixo overlap de board acima do threshold.
    - carry diferente ainda pode representar o mesmo arquétipo quando
      traits e board têm forte sobreposição estrutural.

    O objetivo não é produzir menos clusters. É reduzir merges falsos
    sem perder variantes claramente relacionadas.
    """

    CARRY_WEIGHT = 0.35
    TANK_WEIGHT = 0.10
    TRAIT_WEIGHT = 0.30
    UNIT_WEIGHT = 0.25

    STRUCTURAL_VARIANT_BONUS = 12.5

    @classmethod
    def compare(
        cls,
        first: CompositionSnapshot,
        second: CompositionSnapshot,
    ) -> CompositionSimilarityV2Result:
        same_carry = bool(
            first.carry_character_id
            and first.carry_character_id
            == second.carry_character_id
        )

        same_tank = bool(
            first.tank_character_id
            and first.tank_character_id
            == second.tank_character_id
        )

        carry_score = (
            100.0
            if same_carry
            else 0.0
        )

        tank_score = (
            100.0
            if same_tank
            else 0.0
        )

        first_traits = set(
            first.trait_names
        )
        second_traits = set(
            second.trait_names
        )

        first_units = set(
            first.unit_ids
        )
        second_units = set(
            second.unit_ids
        )

        shared_traits = tuple(
            sorted(
                first_traits
                & second_traits
            )
        )

        shared_units = tuple(
            sorted(
                first_units
                & second_units
            )
        )

        trait_score = cls._dice_percentage(
            first_traits,
            second_traits,
        )

        unit_score = cls._dice_percentage(
            first_units,
            second_units,
        )

        base_score = (
            carry_score
            * cls.CARRY_WEIGHT
            + tank_score
            * cls.TANK_WEIGHT
            + trait_score
            * cls.TRAIT_WEIGHT
            + unit_score
            * cls.UNIT_WEIGHT
        )

        structural_bonus = 0.0

        # Variantes de um mesmo arquétipo podem trocar o carry principal.
        # Só damos bônus quando a estrutura restante é realmente forte.
        if (
            not same_carry
            and trait_score >= 95.0
            and unit_score >= 60.0
        ):
            structural_bonus = (
                cls.STRUCTURAL_VARIANT_BONUS
            )

        score = min(
            base_score
            + structural_bonus,
            100.0,
        )

        cap_applied = False
        reason = ""

        # Proteção contra o falso merge observado na auditoria:
        # trait igual + carry diferente + pouquíssimas unidades em comum.
        if (
            not same_carry
            and unit_score < 50.0
        ):
            capped = min(
                score,
                49.99,
            )

            if capped < score:
                cap_applied = True

            score = capped
            reason = (
                "Carry diferente e overlap de core units abaixo de 50%; "
                "traits compartilhadas não bastam para tratar como "
                "o mesmo arquétipo."
            )

        elif (
            not same_carry
            and trait_score < 95.0
            and unit_score < 65.0
        ):
            capped = min(
                score,
                54.99,
            )

            if capped < score:
                cap_applied = True

            score = capped
            reason = (
                "Carry diferente sem combinação forte de traits e "
                "core units; mantido abaixo do threshold de merge."
            )

        elif (
            structural_bonus > 0.0
        ):
            reason = (
                "Carry diferente, mas traits e core units apresentam "
                "forte sobreposição estrutural; tratado como possível "
                "variante do mesmo arquétipo."
            )

        elif same_carry:
            reason = (
                "Carry principal preservado; similaridade restante "
                "define o grau de proximidade da variante."
            )

        else:
            reason = (
                "Similaridade calculada pela estrutura observada do "
                "board final."
            )

        return CompositionSimilarityV2Result(
            score=round(
                score,
                2,
            ),
            carry_score=round(
                carry_score,
                2,
            ),
            tank_score=round(
                tank_score,
                2,
            ),
            trait_score=round(
                trait_score,
                2,
            ),
            unit_score=round(
                unit_score,
                2,
            ),
            structural_bonus=round(
                structural_bonus,
                2,
            ),
            compatibility_cap_applied=(
                cap_applied
            ),
            compatibility_reason=reason,
            shared_trait_names=shared_traits,
            shared_unit_ids=shared_units,
            same_carry=same_carry,
            same_tank=same_tank,
        )

    @staticmethod
    def _dice_percentage(
        first: set[str],
        second: set[str],
    ) -> float:
        if not first and not second:
            return 0.0

        denominator = (
            len(first)
            + len(second)
        )

        if denominator <= 0:
            return 0.0

        return (
            2.0
            * len(
                first
                & second
            )
            / denominator
            * 100.0
        )
