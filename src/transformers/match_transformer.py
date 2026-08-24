from typing import Any

from src.performance_engine.models import (
    AugmentSnapshot,
    Match,
    ParticipantSnapshot,
    TraitSnapshot,
    UnitSnapshot,
)


class MatchTransformer:
    """
    Converte o JSON da Riot em um Match completo.

    Preserva os participantes, unidades, traits, itens e augments finais.
    """

    @classmethod
    def transform(
        cls,
        match_data: dict[str, Any],
        puuid: str,
    ) -> Match:
        if not match_data:
            raise ValueError(
                "Os dados da partida devem ser informados."
            )

        if not puuid.strip():
            raise ValueError(
                "O PUUID do jogador deve ser informado."
            )

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = str(
            metadata.get("match_id", "")
        ).strip()

        if not match_id:
            raise ValueError(
                "A partida não possui match_id válido."
            )

        raw_participants = info.get("participants", [])

        if not isinstance(raw_participants, list):
            raise ValueError(
                "A partida não possui uma lista válida de participantes."
            )

        participants = tuple(
            cls._transform_participant(participant)
            for participant in raw_participants
            if isinstance(participant, dict)
        )

        analyzed_participant = next(
            (
                participant
                for participant in participants
                if participant.puuid == puuid
            ),
            None,
        )

        if analyzed_participant is None:
            raise ValueError(
                "O jogador não foi encontrado entre os participantes."
            )

        return Match(
            match_id=match_id,
            placement=analyzed_participant.placement,
            level=analyzed_participant.level,
            gold_left=analyzed_participant.gold_left,
            last_round=analyzed_participant.last_round,
            players_eliminated=(
                analyzed_participant.players_eliminated
            ),
            total_damage_to_players=(
                analyzed_participant.total_damage_to_players
            ),
            time_eliminated=(
                analyzed_participant.time_eliminated
            ),
            analyzed_player_puuid=puuid,
            participants=participants,
        )

    @classmethod
    def _transform_participant(
        cls,
        participant: dict[str, Any],
    ) -> ParticipantSnapshot:
        puuid = str(participant.get("puuid", "")).strip()

        if not puuid:
            raise ValueError(
                "Um participante não possui PUUID válido."
            )

        return ParticipantSnapshot(
            puuid=puuid,
            riot_id_game_name=str(
                participant.get("riotIdGameName", "") or ""
            ).strip(),
            riot_id_tag_line=str(
                participant.get("riotIdTagline", "") or ""
            ).strip(),
            placement=cls._to_int(
                participant.get("placement"),
                default=8,
            ),
            level=max(
                cls._to_int(
                    participant.get("level"),
                    default=1,
                ),
                1,
            ),
            gold_left=cls._to_int(
                participant.get("gold_left")
            ),
            last_round=cls._to_int(
                participant.get("last_round")
            ),
            players_eliminated=cls._to_int(
                participant.get("players_eliminated")
            ),
            total_damage_to_players=cls._to_int(
                participant.get("total_damage_to_players")
            ),
            time_eliminated=cls._to_float(
                participant.get("time_eliminated")
            ),
            traits=cls._transform_traits(
                participant.get("traits", [])
            ),
            units=cls._transform_units(
                participant.get("units", [])
            ),
            augments=cls._transform_augments(
                participant.get("augments", [])
            ),
        )

    @classmethod
    def _transform_traits(
        cls,
        raw_traits: Any,
    ) -> tuple[TraitSnapshot, ...]:
        if not isinstance(raw_traits, list):
            return ()

        traits = []

        for raw_trait in raw_traits:
            if not isinstance(raw_trait, dict):
                continue

            name = str(
                raw_trait.get("name", "") or ""
            ).strip()

            if not name:
                continue

            traits.append(
                TraitSnapshot(
                    name=name,
                    num_units=cls._to_int(
                        raw_trait.get("num_units")
                    ),
                    style=cls._to_int(
                        raw_trait.get("style")
                    ),
                    tier_current=cls._to_int(
                        raw_trait.get("tier_current")
                    ),
                    tier_total=cls._to_int(
                        raw_trait.get("tier_total")
                    ),
                )
            )

        return tuple(traits)

    @classmethod
    def _transform_units(
        cls,
        raw_units: Any,
    ) -> tuple[UnitSnapshot, ...]:
        if not isinstance(raw_units, list):
            return ()

        units = []

        for raw_unit in raw_units:
            if not isinstance(raw_unit, dict):
                continue

            character_id = str(
                raw_unit.get("character_id", "") or ""
            ).strip()

            if not character_id:
                continue

            raw_items = raw_unit.get("itemNames", [])

            items = (
                tuple(
                    str(item).strip()
                    for item in raw_items
                    if isinstance(item, str) and item.strip()
                )
                if isinstance(raw_items, list)
                else ()
            )

            units.append(
                UnitSnapshot(
                    character_id=character_id,
                    name=str(
                        raw_unit.get("name", "") or ""
                    ).strip(),
                    rarity=cls._to_int(
                        raw_unit.get("rarity")
                    ),
                    tier=max(
                        cls._to_int(
                            raw_unit.get("tier"),
                            default=1,
                        ),
                        1,
                    ),
                    items=items,
                )
            )

        return tuple(units)

    @staticmethod
    def _transform_augments(
        raw_augments: Any,
    ) -> tuple[AugmentSnapshot, ...]:
        if not isinstance(raw_augments, list):
            return ()

        return tuple(
            AugmentSnapshot(name=augment.strip())
            for augment in raw_augments
            if isinstance(augment, str) and augment.strip()
        )

    @staticmethod
    def _to_int(
        value: Any,
        *,
        default: int = 0,
    ) -> int:
        try:
            converted = int(value)
        except (TypeError, ValueError):
            return default

        return max(converted, 0)

    @staticmethod
    def _to_float(
        value: Any,
        *,
        default: float = 0.0,
    ) -> float:
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return default

        return max(converted, 0.0)
