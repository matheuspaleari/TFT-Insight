"""
Transformação das unidades utilizadas pelos jogadores.
"""

from typing import Any


class UnitTransformer:
    """
    Responsável por transformar as unidades dos participantes.
    """

    @staticmethod
    def transform(
        match_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extrai as unidades utilizadas por cada participante.
        """

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = metadata.get("match_id")
        participants = info.get("participants", [])

        units_rows: list[dict[str, Any]] = []

        for participant in participants:
            puuid = participant.get("puuid")
            units = participant.get("units", [])

            for unit_position, unit in enumerate(
                units,
                start=1
            ):
                items = unit.get("itemNames", [])

                units_rows.append(
                    {
                        "match_id": match_id,
                        "puuid": puuid,
                        "unit_position": unit_position,
                        "character_id": unit.get("character_id"),
                        "unit_name": unit.get("name"),
                        "rarity": unit.get("rarity"),
                        "tier": unit.get("tier"),
                        "item_1": (
                            items[0]
                            if len(items) > 0
                            else None
                        ),
                        "item_2": (
                            items[1]
                            if len(items) > 1
                            else None
                        ),
                        "item_3": (
                            items[2]
                            if len(items) > 2
                            else None
                        ),
                    }
                )

        return units_rows