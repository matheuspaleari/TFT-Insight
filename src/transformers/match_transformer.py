"""
Transformação dos dados gerais das partidas.
"""

from typing import Any


class MatchTransformer:
    """
    Responsável por transformar os dados gerais de uma partida.
    """

    @staticmethod
    def transform(
        match_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extrai os dados gerais da partida.
        """

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        return {
            "match_id": metadata.get("match_id"),
            "game_creation": info.get("gameCreation"),
            "game_datetime": info.get("game_datetime"),
            "game_length": info.get("game_length"),
            "game_version": info.get("game_version"),
            "queue_id": info.get(
                "queue_id",
                info.get("queueId")
            ),
            "tft_game_type": info.get("tft_game_type"),
            "tft_set_core_name": info.get(
                "tft_set_core_name"
            ),
            "tft_set_number": info.get("tft_set_number"),
        }