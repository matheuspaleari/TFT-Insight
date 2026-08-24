from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

load_dotenv(
    PROJECT_ROOT / ".env"
)


from src.benchmark import (
    LeaguePlayerProvider,
)
from src.riot_client import RiotClient


def main() -> None:
    provider = LeaguePlayerProvider(
        riot_client=RiotClient()
    )

    players = provider.get_players(
        benchmark_id="intermediate"
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - LEAGUE PLAYER PROVIDER")
    print("=" * 80)

    print()
    print(
        f"Candidatos encontrados: "
        f"{len(players)}"
    )

    print()

    for index, player in enumerate(
        players[:20],
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{player.rank_label:<14} "
            f"LP: {player.league_points:<5} "
            f"Partidas: {player.games_played:<4} "
            f"PUUID: {player.puuid[:16]}..."
        )

    if not players:
        raise AssertionError(
            "Nenhum candidato foi encontrado."
        )

    if len(
        {
            player.puuid
            for player in players
        }
    ) != len(players):
        raise AssertionError(
            "O Provider retornou PUUIDs duplicados."
        )

    tiers = {
        player.tier
        for player in players
    }

    if not tiers.issubset(
        {
            "GOLD",
            "PLATINUM",
        }
    ):
        raise AssertionError(
            "O benchmark intermediate retornou "
            "jogadores de elos inesperados."
        )

    print()
    print(
        "✓ Provider validado com sucesso."
    )


if __name__ == "__main__":
    main()