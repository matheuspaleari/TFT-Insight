"""
Transformação das traits utilizadas pelos jogadores.
"""

from typing import Any


class TraitTransformer:
    """
    Responsável por transformar as traits dos participantes.
    """

    @staticmethod
    def transform(
        match_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extrai as traits utilizadas por cada participante.
        """

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = metadata.get("match_id")
        participants = info.get("participants", [])

        traits_rows: list[dict[str, Any]] = []

        for participant in participants:
            puuid = participant.get("puuid")
            traits = participant.get("traits", [])

            for trait in traits:
                traits_rows.append(
                    {
                        "match_id": match_id,
                        "puuid": puuid,
                        "trait_name": trait.get("name"),
                        "num_units": trait.get("num_units"),
                        "style": trait.get("style"),
                        "tier_current": trait.get(
                            "tier_current"
                        ),
                        "tier_total": trait.get(
                            "tier_total"
                        ),
                    }
                )

        return traits_rows