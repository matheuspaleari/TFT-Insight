"""
Valida identidade e clustering de composições usando partidas reais.
"""

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


from src.decision_engine import (
    CompositionAnalyzer,
    CompositionClusterAnalyzer,
    CompositionHistoryAnalyzer,
    CompositionSimilarityAnalyzer,
    ContestHistoryAnalyzer,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


MATCH_COUNT = 10


def main() -> None:
    game_name = input(
        "Nome do jogador: "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    client = RiotClient()

    account = client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = account["puuid"]

    match_ids = client.get_match_ids(
        puuid=puuid,
        count=MATCH_COUNT,
    )

    matches = []

    for index, match_id in enumerate(
        match_ids,
        start=1,
    ):
        print(
            f"Processando partida "
            f"{index}/{len(match_ids)}..."
        )

        try:
            match_data = client.get_match_details(
                match_id=match_id,
            )

            matches.append(
                MatchTransformer.transform(
                    match_data=match_data,
                    puuid=puuid,
                )
            )

        except (
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            print(
                f"Partida {match_id} ignorada: "
                f"{error}"
            )

    if not matches:
        raise RuntimeError(
            "Nenhuma partida válida foi processada."
        )

    snapshots = tuple(
        CompositionAnalyzer.analyze(match)
        for match in matches
    )

    clusters = (
        CompositionClusterAnalyzer.cluster(
            snapshots
        )
    )

    contest_history = (
        ContestHistoryAnalyzer.analyze(
            matches
        )
    )

    history = (
        CompositionHistoryAnalyzer.analyze(
            matches,
            contest_history=contest_history,
        )
    )

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - COMPOSITION IDENTITY"
    )
    print("=" * 80)

    print(
        f"Partidas analisadas : "
        f"{len(matches)}"
    )
    print(
        f"Identidades         : "
        f"{len(clusters)}"
    )
    print(
        f"Taxa de repetição   : "
        f"{history.repetition_rate:.2f}%"
    )
    print(
        f"Taxa de diversidade : "
        f"{history.diversity_rate:.2f}%"
    )

    for cluster in clusters:
        identity = cluster.representative

        print()
        print("-" * 80)
        print(cluster.cluster_id.upper())
        print(
            f"Partidas       : "
            f"{cluster.matches_played}"
        )
        print(
            f"Traits principais: "
            f"{', '.join(identity.trait_names) or '-'}"
        )
        print(
            f"Carry inferido : "
            f"{identity.carry_character_id or '-'}"
        )
        print(
            f"Unidades core  : "
            f"{', '.join(identity.unit_ids) or '-'}"
        )

        if cluster.matches_played > 1:
            representative = (
                cluster.representative
            )

            similarities = [
                CompositionSimilarityAnalyzer.compare(
                    representative,
                    snapshot,
                ).score
                for snapshot in cluster.snapshots
                if snapshot.match_id
                != representative.match_id
            ]

            if similarities:
                print(
                    f"Similaridade média: "
                    f"{sum(similarities) / len(similarities):.2f}%"
                )

    print()
    print(
        "✓ Composition Identity validada com sucesso."
    )


if __name__ == "__main__":
    main()
