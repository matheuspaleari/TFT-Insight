"""
Valida a análise histórica de contestação com partidas reais.
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
    ContestHistoryAnalyzer,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


MATCH_COUNT = 10


def _format_optional_placement(
    value: float | None,
) -> str:
    if value is None:
        return "-"

    return f"{value:.2f}"


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

    if not match_ids:
        raise RuntimeError(
            "Nenhuma partida encontrada."
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
            match_data = (
                client.get_match_details(
                    match_id=match_id,
                )
            )

            match = MatchTransformer.transform(
                match_data=match_data,
                puuid=puuid,
            )

            matches.append(match)

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

    report = ContestHistoryAnalyzer.analyze(
        matches
    )

    latest = report.latest_report

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - CONTEST HISTORY"
    )
    print("=" * 80)

    print()
    print("VISÃO GERAL")
    print("-" * 80)
    print(
        f"Partidas analisadas             : "
        f"{report.matches_analyzed}"
    )
    print(
        f"Score médio                     : "
        f"{report.average_score:.2f}"
    )
    print(
        f"Classificação geral             : "
        f"{report.level.value}"
    )
    print(
        f"Maior score                     : "
        f"{report.highest_score:.2f}"
    )
    print(
        f"Contestação alta ou extrema     : "
        f"{report.high_contest_rate:.2f}% "
        f"({report.high_contest_matches} partidas)"
    )
    print(
        f"Carry contestado                : "
        f"{report.carry_contest_rate:.2f}% "
        f"({report.carry_contested_matches} partidas)"
    )
    print(
        f"Colocação média                 : "
        f"{report.average_placement:.2f}"
    )
    print(
        f"Colocação média contestado      : "
        f"{_format_optional_placement(report.contested_average_placement)}"
    )
    print(
        f"Colocação média não contestado  : "
        f"{_format_optional_placement(report.uncontested_average_placement)}"
    )
    print(
        f"Impacto observado               : "
        f"{report.placement_impact if report.placement_impact is not None else '-'}"
    )
    print(
        f"Unidade mais contestada         : "
        f"{report.most_contested_unit_id or '-'}"
    )
    print(
        f"Trait mais contestada           : "
        f"{report.most_contested_trait_name or '-'}"
    )

    print()
    print("ÚLTIMA PARTIDA")
    print("-" * 80)
    print(
        f"Partida                         : "
        f"{latest.match_id}"
    )
    print(
        f"Score                           : "
        f"{latest.score:.2f}"
    )
    print(
        f"Classificação                   : "
        f"{latest.level.value}"
    )
    print(
        f"Carry                           : "
        f"{latest.carry_character_id or '-'}"
    )
    print(
        f"Carry contestado                : "
        f"{'Sim' if latest.carry_contested else 'Não'}"
    )
    print(
        f"Adversários com unidades        : "
        f"{latest.opponents_with_shared_units}"
    )
    print(
        f"Adversários com traits          : "
        f"{latest.opponents_with_shared_traits}"
    )

    if report.matches_analyzed != len(matches):
        raise AssertionError(
            "O relatório não consolidou todas as partidas."
        )

    print()
    print(
        "✓ ContestHistoryAnalyzer validado com sucesso."
    )


if __name__ == "__main__":
    main()
