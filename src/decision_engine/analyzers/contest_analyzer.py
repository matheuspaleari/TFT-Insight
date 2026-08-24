"""
Analisador híbrido de contestação da composição final.
"""

from collections import Counter

from src.decision_engine.constants.contest_weights import (
    CARRY_CONTEST_WEIGHT,
    TRAIT_OVERLAP_WEIGHT,
    UNIT_OVERLAP_WEIGHT,
)
from src.decision_engine.models import (
    ContestLevel,
    ContestReport,
    ParticipantOverlap,
)
from src.performance_engine.models import (
    Match,
    ParticipantSnapshot,
    TraitSnapshot,
    UnitSnapshot,
)


class ContestAnalyzer:
    """
    Calcula contestação usando unidades, traits relevantes e carry.

    A análise representa somente o estado final dos tabuleiros.
    Ela não reconstrói a contestação durante toda a partida.

    Ajustes desta versão:

    - ignora traits técnicas ou individuais de campeão;
    - ignora traits genéricas de função que não definem composição;
    - só pontua sobreposição de unidades quando existem ao menos
      duas unidades compartilhadas;
    - mantém a contestação do carry como evidência independente.
    """

    MIN_SHARED_UNITS_FOR_COMPOSITION = 2

    IGNORED_TRAIT_EXACT_NAMES = frozenset(
        {
            "TFT17_ResistTank",
            "TFT17_ShieldTank",
        }
    )

    IGNORED_TRAIT_NAME_PARTS = (
        "UniqueTrait",
        "Role",
    )

    @classmethod
    def analyze(
        cls,
        match: Match,
    ) -> ContestReport:
        """
        Analisa a contestação do jogador principal em uma partida.
        """

        player = match.analyzed_participant

        if player is None:
            raise ValueError(
                "O Match não possui participante analisado."
            )

        carry = cls._select_carry(
            player
        )

        overlaps = tuple(
            cls._build_overlap(
                player=player,
                opponent=opponent,
                carry=carry,
            )
            for opponent in match.opponents
        )

        overall_score = max(
            (
                overlap.score
                for overlap in overlaps
            ),
            default=0.0,
        )

        contested_unit_counts = Counter(
            unit_id
            for overlap in overlaps
            for unit_id in overlap.shared_unit_ids
        )

        contested_trait_counts = Counter(
            trait_name
            for overlap in overlaps
            for trait_name in overlap.shared_trait_names
        )

        contested_unit_ids = tuple(
            unit_id
            for unit_id, count
            in contested_unit_counts.most_common()
            if count > 0
        )

        contested_trait_names = tuple(
            trait_name
            for trait_name, count
            in contested_trait_counts.most_common()
            if count > 0
        )

        opponents_contesting_carry = sum(
            1
            for overlap in overlaps
            if overlap.carry_contested
        )

        carry_character_id = (
            carry.character_id
            if carry is not None
            else ""
        )

        return ContestReport(
            match_id=match.match_id,
            analyzed_player_puuid=(
                match.analyzed_player_puuid
            ),
            score=round(
                overall_score,
                2,
            ),
            level=ContestLevel.from_score(
                overall_score
            ),
            carry_character_id=(
                carry_character_id
            ),
            carry_contested=(
                opponents_contesting_carry > 0
            ),
            contested_unit_ids=(
                contested_unit_ids
            ),
            contested_trait_names=(
                contested_trait_names
            ),
            opponents_with_shared_units=sum(
                1
                for overlap in overlaps
                if overlap.shared_units_count > 0
            ),
            opponents_with_shared_traits=sum(
                1
                for overlap in overlaps
                if overlap.shared_traits_count > 0
            ),
            opponents_contesting_carry=(
                opponents_contesting_carry
            ),
            overlaps=overlaps,
        )

    @classmethod
    def _build_overlap(
        cls,
        *,
        player: ParticipantSnapshot,
        opponent: ParticipantSnapshot,
        carry: UnitSnapshot | None,
    ) -> ParticipantOverlap:
        player_unit_ids = player.unit_ids
        opponent_unit_ids = opponent.unit_ids

        player_trait_names = (
            cls._relevant_trait_names(
                player
            )
        )
        opponent_trait_names = (
            cls._relevant_trait_names(
                opponent
            )
        )

        shared_unit_ids = tuple(
            sorted(
                player_unit_ids
                & opponent_unit_ids
            )
        )

        shared_trait_names = tuple(
            sorted(
                player_trait_names
                & opponent_trait_names
            )
        )

        raw_unit_overlap_percentage = (
            cls._percentage(
                numerator=len(shared_unit_ids),
                denominator=len(player_unit_ids),
            )
        )

        if (
            len(shared_unit_ids)
            >= cls.MIN_SHARED_UNITS_FOR_COMPOSITION
        ):
            scored_unit_overlap_percentage = (
                raw_unit_overlap_percentage
            )
        else:
            scored_unit_overlap_percentage = 0.0

        trait_overlap_percentage = (
            cls._percentage(
                numerator=len(
                    shared_trait_names
                ),
                denominator=len(
                    player_trait_names
                ),
            )
        )

        carry_character_id = (
            carry.character_id
            if carry is not None
            else ""
        )

        carry_contested = (
            bool(carry_character_id)
            and carry_character_id
            in opponent_unit_ids
        )

        carry_percentage = (
            100.0
            if carry_contested
            else 0.0
        )

        score = (
            scored_unit_overlap_percentage
            * UNIT_OVERLAP_WEIGHT
            + trait_overlap_percentage
            * TRAIT_OVERLAP_WEIGHT
            + carry_percentage
            * CARRY_CONTEST_WEIGHT
        )

        return ParticipantOverlap(
            opponent_puuid=opponent.puuid,
            opponent_riot_id=opponent.riot_id,
            shared_unit_ids=shared_unit_ids,
            shared_trait_names=(
                shared_trait_names
            ),
            unit_overlap_percentage=round(
                raw_unit_overlap_percentage,
                2,
            ),
            trait_overlap_percentage=round(
                trait_overlap_percentage,
                2,
            ),
            carry_contested=(
                carry_contested
            ),
            carry_character_id=(
                carry_character_id
                if carry_contested
                else ""
            ),
            score=round(
                score,
                2,
            ),
            level=ContestLevel.from_score(
                score
            ),
        )

    @classmethod
    def _relevant_trait_names(
        cls,
        participant: ParticipantSnapshot,
    ) -> frozenset[str]:
        """
        Retorna somente traits ativas que ajudam a definir composição.
        """

        return frozenset(
            trait.name
            for trait in participant.active_traits
            if cls._is_relevant_trait(
                trait
            )
        )

    @classmethod
    def _is_relevant_trait(
        cls,
        trait: TraitSnapshot,
    ) -> bool:
        """
        Remove traits técnicas, individuais e genéricas de função.
        """

        trait_name = trait.name.strip()

        if not trait_name:
            return False

        if (
            trait_name
            in cls.IGNORED_TRAIT_EXACT_NAMES
        ):
            return False

        if any(
            ignored_part in trait_name
            for ignored_part
            in cls.IGNORED_TRAIT_NAME_PARTS
        ):
            return False

        return True

    @staticmethod
    def _select_carry(
        participant: ParticipantSnapshot,
    ) -> UnitSnapshot | None:
        """
        Infere o carry final.

        Prioridade:

        1. maior quantidade de itens;
        2. maior tier de estrela;
        3. maior raridade;
        4. character_id para desempate estável.
        """

        if not participant.units:
            return None

        return max(
            participant.units,
            key=lambda unit: (
                len(unit.items),
                unit.tier,
                unit.rarity,
                unit.character_id,
            ),
        )

    @staticmethod
    def _percentage(
        *,
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return (
            numerator
            / denominator
            * 100.0
        )
