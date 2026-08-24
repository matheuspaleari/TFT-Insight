"""
Valida o CompositionHistoryAnalyzer usando partidas reais.
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
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


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
        "TFT INSIGHT - COMPOSITION HISTORY"
    )
    print("=" * 80)

    print()
    print("VISÃO GERAL")
    print("-" * 80)
    print(
        f"Partidas analisadas      : "
        f"{report.matches_analyzed}"
    )
    print(
        f"Composições únicas       : "
        f"{report.unique_compositions}"
    )
    print(
        f"Taxa de diversidade      : "
        f"{report.diversity_rate:.2f}%"
    )
    print(
        f"Taxa de repetição        : "
        f"{report.repetition_rate:.2f}%"
    )
    print(
        f"Força composição?        : "
        f"{'Possível padrão' if report.forces_composition else 'Não identificado'}"
    )

    print()
    print("MAIS UTILIZADA")
    print("-" * 80)
    most_used = (
        report.most_used_composition
    )
    print(
        f"Carry                    : "
        f"{most_used.carry_character_id or '-'}"
    )
    print(
        f"Partidas                 : "
        f"{most_used.matches_played}"
    )
    print(
        f"Uso                      : "
        f"{most_used.usage_rate:.2f}%"
    )
    print(
        f"Colocação média          : "
        f"{most_used.average_placement:.2f}"
    )
    print(
        f"Top 4                    : "
        f"{most_used.top4_rate:.2f}%"
    )
    print(
        f"Contestação média        : "
        f"{most_used.average_contest_score if most_used.average_contest_score is not None else '-'}"
    )

    print()
    print("MELHOR COMPOSIÇÃO")
    print("-" * 80)
    best = report.best_composition
    print(
        f"Carry                    : "
        f"{best.carry_character_id or '-'}"
    )
    print(
        f"Colocação média          : "
        f"{best.average_placement:.2f}"
    )
    print(
        f"Partidas                 : "
        f"{best.matches_played}"
    )

    print()
    print("ÚLTIMA PARTIDA")
    print("-" * 80)
    latest = report.latest_composition
    print(
        f"Carry                    : "
        f"{latest.carry_character_id or '-'}"
    )
    print(
        f"Traits                   : "
        f"{', '.join(latest.trait_names) or '-'}"
    )
    print(
        f"Colocação                : "
        f"{latest.placement}"
    )

    print()
    print(
        "✓ CompositionHistoryAnalyzer validado com sucesso."
    )


if __name__ == "__main__":
    main()
