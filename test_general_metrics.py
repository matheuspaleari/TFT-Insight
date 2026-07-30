from src.performance_engine.calculators import PlayerMetricsCalculator
from src.riot_client import RiotClient
from src.transformers import MatchTransformer


def main() -> None:
    client = RiotClient()

    game_name = "Pinador Doss"
    tag_line = "000"

    puuid = client.get_puuid(
        game_name=game_name,
        tag_line=tag_line,
    )

    match_ids = client.get_match_ids(
        puuid=puuid,
        count=5,
    )

    matches = []

    for match_id in match_ids:
        match_data = client.get_match_details(match_id)

        match = MatchTransformer.transform(
            match_data=match_data,
            puuid=puuid,
        )

        matches.append(match)

    metrics = PlayerMetricsCalculator.calculate(matches)

    print("\nMétricas gerais:")
    print(metrics.general)

    print("\nConsistência:")
    print(metrics.consistency)

    print("\nCombate:")
    print(metrics.combat)

    print("\nEconomia:")
    print(metrics.economy)


if __name__ == "__main__":
    main()