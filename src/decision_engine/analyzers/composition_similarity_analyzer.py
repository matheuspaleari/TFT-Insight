"""
Comparação entre duas identidades de composição.
"""

from src.decision_engine.constants.composition_similarity import (
    CARRY_SIMILARITY_WEIGHT,
    TRAIT_SIMILARITY_WEIGHT,
    UNIT_SIMILARITY_WEIGHT,
)
from src.decision_engine.models import (
    CompositionSimilarity,
    CompositionSnapshot,
)


class CompositionSimilarityAnalyzer:
    """
    Compara identidades estratégicas, não tabuleiros completos.

    Pesos:

    - 25% carry;
    - 50% traits principais;
    - 25% unidades core.

    O coeficiente Dice é usado para tolerar pequenas variações.
    """

    @classmethod
    def compare(
        cls,
        first: CompositionSnapshot,
        second: CompositionSnapshot,
    ) -> CompositionSimilarity:
        carry_score = (
            100.0
            if (
                first.carry_character_id
                and first.carry_character_id
                == second.carry_character_id
            )
            else 0.0
        )

        first_traits = set(first.trait_names)
        second_traits = set(second.trait_names)

        shared_traits = tuple(
            sorted(
                first_traits
                & second_traits
            )
        )

        trait_score = cls._dice_percentage(
            first_traits,
            second_traits,
        )

        first_units = set(first.unit_ids)
        second_units = set(second.unit_ids)

        shared_units = tuple(
            sorted(
                first_units
                & second_units
            )
        )

        unit_score = cls._dice_percentage(
            first_units,
            second_units,
        )

        score = (
            carry_score
            * CARRY_SIMILARITY_WEIGHT
            + trait_score
            * TRAIT_SIMILARITY_WEIGHT
            + unit_score
            * UNIT_SIMILARITY_WEIGHT
        )

        return CompositionSimilarity(
            score=round(score, 2),
            carry_score=round(carry_score, 2),
            trait_score=round(trait_score, 2),
            unit_score=round(unit_score, 2),
            shared_trait_names=shared_traits,
            shared_unit_ids=shared_units,
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

        if denominator == 0:
            return 0.0

        return (
            2
            * len(first & second)
            / denominator
            * 100.0
        )
