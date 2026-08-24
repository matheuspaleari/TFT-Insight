from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.riot_client import RiotClient
from src.benchmark import BenchmarkSelector


def main() -> None:

    client = RiotClient()

    account = client.get_account(
        game_name="Pinador Doss",
        tag_line="000",
    )

    puuid = account["puuid"]

    tier = client.get_current_tft_tier(
        puuid=puuid,
    )

    print("=" * 70)

    if tier is None:
        print("Jogador sem elo.")
        return

    group = BenchmarkSelector.from_rank(
        tier
    )

    print(f"Elo Riot        : {tier}")
    print(f"Grupo           : {group.id}")
    print(f"Estágio         : {group.display_name}")
    print(f"Benchmark       : {group.benchmark_id}")
    print(
        f"Objetivo        : "
        f"{BenchmarkSelector.get_target_display_name(group)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()