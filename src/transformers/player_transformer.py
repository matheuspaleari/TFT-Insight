"""
Transformação dos dados dos jogadores.
"""

from typing import Any


class PlayerTransformer:
    """
    Responsável por transformar os participantes das partidas.
    """

    @staticmethod
    def transform(
        match_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extrai os dados dos participantes da partida.
        """

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = metadata.get("match_id")
        participants = info.get("participants", [])

        players_rows: list[dict[str, Any]] = []

        for participant in participants:
            players_rows.append(
                {
                    "match_id": match_id,
                    "puuid": participant.get("puuid"),
                    "riot_id_game_name": participant.get(
                        "riotIdGameName"
                    ),
                    "riot_id_tagline": participant.get(
                        "riotIdTagline"
                    ),
                    "placement": participant.get("placement"),
                    "level": participant.get("level"),
                    "gold_left": participant.get("gold_left"),
                    "last_round": participant.get("last_round"),
                    "players_eliminated": participant.get(
                        "players_eliminated"
                    ),
                    "time_eliminated": participant.get(
                        "time_eliminated"
                    ),
                    "total_damage_to_players": participant.get(
                        "total_damage_to_players"
                    ),
                    "win": participant.get("win"),
                }
            )

        return players_rows