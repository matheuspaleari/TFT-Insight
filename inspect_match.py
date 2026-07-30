import json

from src.riot_client import RiotClient


def main() -> None:
    client = RiotClient()

    game_name = "Pinador doss"
    tag_line = "000"

    puuid = client.get_puuid(
        game_name=game_name,
        tag_line=tag_line,
    )

    match_ids = client.get_match_ids(
        puuid=puuid,
        count=1,
    )

    if not match_ids:
        print("Nenhuma partida encontrada.")
        return

    match_data = client.get_match_details(match_ids[0])

    participants = match_data["info"]["participants"]

    player_data = next(
        (
            participant
            for participant in participants
            if participant.get("puuid") == puuid
        ),
        None,
    )

    if player_data is None:
        print("Jogador não encontrado na partida.")
        return

    print(json.dumps(player_data, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()