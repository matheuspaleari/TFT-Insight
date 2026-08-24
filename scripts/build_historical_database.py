from pathlib import Path
import sys
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.coaching_engine import HistoricalMatchRepository
from src.riot_client import RiotClient


def main() -> None:
    name = input("Nome do jogador: ").strip()
    tag = input("Tag: ").strip()

    client = RiotClient()
    account = client.get_account(
        game_name=name,
        tag_line=tag,
    )
    puuid = account["puuid"]

    ids = client.get_match_ids(
        puuid=puuid,
        count=100,
    )

    repository = HistoricalMatchRepository()
    saved = 0

    for index, match_id in enumerate(ids, start=1):
        print(f"{index}/{len(ids)} {match_id}")

        if repository.contains(match_id):
            continue

        payload = client.get_match_details(
            match_id=match_id
        )

        saved += int(
            repository.save_raw_match(
                match_id=match_id,
                puuid=puuid,
                payload=payload,
            )
        )

    print(f"Novas partidas salvas: {saved}")
    print("Base: data/history/matches.jsonl")


if __name__ == "__main__":
    main()
