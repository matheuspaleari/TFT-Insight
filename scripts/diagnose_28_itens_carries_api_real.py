from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from partner_platform.services.api_client import DashboardApiClient


def main() -> None:
    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    client = DashboardApiClient(
        base_url=os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        api_key=os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ),
        timeout=300.0,
    )

    payload = client.carry_item_intelligence(
        game_name=game_name,
        tag_line=tag_line,
        match_count=30,
    )

    summary = payload.get("summary", {}) or {}
    latest = payload.get("latest")
    most = payload.get("most_used_carry")
    best = payload.get("best_supported_carry")

    print()
    print("=" * 108)
    print("#28 ITENS + CARRIES - API REAL")
    print("=" * 108)
    print(f"Jogador                  : {game_name}#{tag_line}")
    print(f"Partidas                 : {summary.get('matches_analyzed', '-')}")
    print(
        f"Carry identificado       : {summary.get('matches_with_carry', '-')} "
        f"({summary.get('carry_detection_rate', '-')}%)"
    )
    print(f"Carries únicos           : {summary.get('unique_carries', '-')}")
    print(
        f"Itemização               : {summary.get('itemization_score', '-')} · "
        f"{summary.get('itemization_label', '-')}"
    )
    print(f"Carry item share         : {summary.get('carry_item_share', '-')}%")
    print(f"Carry 3+ itens           : {summary.get('carry_full_item_rate', '-')}%")

    print()
    print("ÚLTIMA PARTIDA")
    print("-" * 108)
    if isinstance(latest, dict):
        print(f"Carry                    : {latest.get('character_id', '-')}")
        print(f"Itens                    : {', '.join(latest.get('item_ids', []) or []) or '-'}")
        print(f"Colocação                : {latest.get('placement', '-')}")
    else:
        print("Carry não identificado.")

    print()
    print("MAIS USADO")
    print("-" * 108)
    if isinstance(most, dict):
        print(f"Carry                    : {most.get('character_id', '-')}")
        print(f"Partidas                 : {most.get('matches_played', '-')}")
        print(f"Média                    : {most.get('average_placement', '-')}")
        print(f"Top4                     : {most.get('top4_rate', '-')}%")
        print("Itens recorrentes:")
        for item in (most.get("most_used_items", []) or [])[:6]:
            print(
                f"- {item.get('item_id')} · "
                f"{item.get('matches_observed')} partida(s) · "
                f"{item.get('match_rate')}%"
            )
        print("Builds:")
        for build in (most.get("recurring_builds", []) or [])[:5]:
            print(
                f"- {build.get('item_ids')} · "
                f"{build.get('matches_played')} partida(s) · "
                f"média {build.get('average_placement')} · "
                f"elegível={build.get('eligible_for_comparison')}"
            )
    else:
        print("Nenhum carry identificado.")

    print()
    print("MELHOR COM AMOSTRA MÍNIMA")
    print("-" * 108)
    if isinstance(best, dict):
        print(f"Carry                    : {best.get('character_id', '-')}")
        print(f"Partidas                 : {best.get('matches_played', '-')}")
        print(f"Média                    : {best.get('average_placement', '-')}")
        print(f"Top4                     : {best.get('top4_rate', '-')}%")
    else:
        print("Nenhum carry atingiu 3 partidas.")

    print()
    print("COACH")
    print("-" * 108)
    coach = payload.get("coach", {}) or {}
    for item in coach.get("observations", []):
        print("-", item)

    print()
    print("=" * 108)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde '#28 ITENS + CARRIES - API REAL' até o final.")
    print("=" * 108)


if __name__ == "__main__":
    main()
