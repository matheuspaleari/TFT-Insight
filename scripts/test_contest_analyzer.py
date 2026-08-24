"""
Valida o ContestAnalyzer usando uma partida real da Riot API.
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
    ContestAnalyzer,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


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

    report = ContestAnalyzer.analyze(
        match
    )

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - CONTEST ANALYZER"
    )
    print("=" * 80)

    print()
    print(
        f"Partida                 : "
        f"{report.match_id}"
    )
    print(
        f"Score de contestação    : "
        f"{report.score:.2f}"
    )
    print(
        f"Classificação           : "
        f"{report.level.value}"
    )
    print(
        f"Carry inferido          : "
        f"{report.carry_character_id or '-'}"
    )
    print(
        f"Carry contestado        : "
        f"{'Sim' if report.carry_contested else 'Não'}"
    )
    print(
        f"Adversários no carry    : "
        f"{report.opponents_contesting_carry}"
    )
    print(
        f"Adversários com units   : "
        f"{report.opponents_with_shared_units}"
    )
    print(
        f"Adversários com traits  : "
        f"{report.opponents_with_shared_traits}"
    )

    print()
    print("UNIDADES CONTESTADAS")
    print("-" * 80)

    if report.contested_unit_ids:
        for unit_id in (
            report.contested_unit_ids
        ):
            print(f"• {unit_id}")
    else:
        print("Nenhuma.")

    print()
    print("TRAITS CONTESTADAS")
    print("-" * 80)

    if report.contested_trait_names:
        for trait_name in (
            report.contested_trait_names
        ):
            print(f"• {trait_name}")
    else:
        print("Nenhuma.")

    worst = report.worst_opponent

    print()
    print("MAIOR SOBREPOSIÇÃO")
    print("-" * 80)

    if worst is None:
        print("Nenhum adversário analisado.")
    else:
        print(
            f"Adversário              : "
            f"{worst.opponent_riot_id or worst.opponent_puuid[:16]}"
        )
        print(
            f"Score                   : "
            f"{worst.score:.2f}"
        )
        print(
            f"Unidades em comum       : "
            f"{worst.shared_units_count}"
        )
        print(
            f"Traits em comum         : "
            f"{worst.shared_traits_count}"
        )
        print(
            f"Carry contestado        : "
            f"{'Sim' if worst.carry_contested else 'Não'}"
        )

    if not report.overlaps:
        raise AssertionError(
            "Nenhum adversário foi analisado."
        )

    print()
    print(
        "✓ ContestAnalyzer validado com sucesso."
    )


if __name__ == "__main__":
    main()
