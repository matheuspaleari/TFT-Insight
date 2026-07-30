from typing import Any

from src.performance_engine.models import Match


class MatchTransformer:
    """
    Converte os dados brutos de uma partida da Riot API
    em um modelo interno Match.

    Esta classe não calcula métricas.
    """

    @staticmethod
    def transform(
        match_data: dict[str, Any],
        puuid: str,
    ) -> Match:
        if not match_data:
            raise ValueError("Os dados da partida devem ser informados.")

        if not puuid:
            raise ValueError("O PUUID do jogador deve ser informado.")

        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = metadata.get("match_id", "")

        participants = info.get("participants", [])

        participant = next(
            (
                participant
                for participant in participants
                if participant.get("puuid") == puuid
            ),
            None,
        )

        if participant is None:
            raise ValueError(
                "O jogador não foi encontrado entre os participantes."
            )

        return Match(
            match_id=match_id,
            placement=participant["placement"],
            level=participant["level"],
            gold_left=participant["gold_left"],
            last_round=participant["last_round"],
            players_eliminated=participant["players_eliminated"],
            total_damage_to_players=participant[
                "total_damage_to_players"
            ],
            time_eliminated=participant["time_eliminated"],
        )