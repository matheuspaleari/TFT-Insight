from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


def main() -> None:
    game_name = input("Nome do jogador: ").strip()
    tag_line = input("Tag: ").strip()

    client = RiotClient()

    account = client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = account["puuid"]

    match_ids = client.get_match_ids(
        puuid=puuid,
        count=1,
    )

    if not match_ids:
        raise RuntimeError(
            "Nenhuma partida encontrada."
        )

    match_data = client.get_match_details(
        match_id=match_ids[0],
    )

    match = MatchTransformer.transform(
        match_data=match_data,
        puuid=puuid,
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - MATCH ENRICHMENT")
    print("=" * 80)
    print(f"Partida       : {match.match_id}")
    print(f"Participantes : {len(match.participants)}")
    print(f"Adversários   : {len(match.opponents)}")

    player = match.analyzed_participant

    if player is None:
        raise AssertionError(
            "Jogador analisado não encontrado."
        )

    print()
    print("JOGADOR ANALISADO")
    print("-" * 80)
    print(f"Colocação : {player.placement}")
    print(f"Nível     : {player.level}")
    print(f"Unidades  : {len(player.units)}")
    print(f"Traits    : {len(player.traits)}")
    print(f"Ativas    : {len(player.active_traits)}")
    print(f"Augments  : {len(player.augments)}")

    if len(match.participants) < 2:
        raise AssertionError(
            "A partida deveria preservar mais de um participante."
        )

    print()
    print("✓ Match enriquecido validado com sucesso.")


if __name__ == "__main__":
    main()
