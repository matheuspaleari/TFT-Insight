"""
Valida o agrupamento de composições usando partidas reais.
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
    CompositionClusterAnalyzer,
    CompositionHistoryAnalyzer,
    CompositionAnalyzer,
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

    report = (
        CompositionHistoryAnalyzer.analyze(
            matches,
            contest_history=contest_history,
        )
    )

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - COMPOSITION CLUSTERING"
    )
    print("=" * 80)

    print()
    print(
        f"Partidas analisadas : "
        f"{len(matches)}"
    )
    print(
        f"Clusters encontrados: "
        f"{len(clusters)}"
    )
    print(
        f"Taxa de repetição   : "
        f"{report.repetition_rate:.2f}%"
    )
    print(
        f"Taxa de diversidade : "
        f"{report.diversity_rate:.2f}%"
    )

    for cluster in clusters:
        representative = (
            cluster.representative
        )

        print()
        print("-" * 80)
        print(
            f"{cluster.cluster_id.upper()}"
        )
        print(
            f"Partidas       : "
            f"{cluster.matches_played}"
        )
        print(
            f"Carry          : "
            f"{representative.carry_character_id or '-'}"
        )
        print(
            f"Traits         : "
            f"{', '.join(representative.trait_names) or '-'}"
        )
        print(
            f"Unidades core  : "
            f"{', '.join(representative.unit_ids[:5]) or '-'}"
        )

    print()
    print(
        "✓ Composition Clustering validado com sucesso."
    )


if __name__ == "__main__":
    main()
