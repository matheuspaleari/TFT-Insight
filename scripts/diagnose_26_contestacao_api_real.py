from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from partner_platform.services.api_client import DashboardApiClient

def main():
    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    client = DashboardApiClient(
        base_url=os.getenv("TFT_INSIGHT_API_BASE_URL", "http://127.0.0.1:8000"),
        api_key=os.getenv("TFT_INSIGHT_API_KEY", ""),
        timeout=300.0,
    )

    payload = client.contest_intelligence(
        game_name=game_name,
        tag_line=tag_line,
        match_count=30,
    )

    summary = payload.get("summary", {}) or {}
    latest = payload.get("latest", {}) or {}
    comparison = payload.get("placement_comparison", {}) or {}
    recurring = payload.get("recurring_pressure", {}) or {}
    coach = payload.get("coach", {}) or {}

    print("\n" + "=" * 108)
    print("#26 CONTESTAÇÃO AVANÇADA - API REAL")
    print("=" * 108)
    print(f"Jogador                  : {game_name}#{tag_line}")
    print(f"Partidas                 : {summary.get('matches_analyzed', '-')}")
    print(f"Contestação média        : {summary.get('average_score', '-')}")
    print(f"Classificação            : {summary.get('level', '-')}")
    print(f"Alta contestação         : {summary.get('high_contest_rate', '-')}%")
    print(f"Carry contestado         : {summary.get('carry_contest_rate', '-')}%")
    print(f"Rivais/carry em média    : {summary.get('average_opponents_contesting_carry', '-')}")

    print("\nÚLTIMA PARTIDA")
    print("-" * 108)
    print(f"Partida                  : {latest.get('match_id', '-')}")
    print(f"Score                    : {latest.get('score', '-')}")
    print(f"Carry                    : {latest.get('carry_character_id', '-')}")
    print(f"Carry contestado         : {latest.get('carry_contested', '-')}")
    print(f"Adversários no carry     : {latest.get('opponents_contesting_carry', '-')}")

    print("\nCOMPARAÇÃO DE COLOCAÇÃO")
    print("-" * 108)
    print(f"Elegível                 : {comparison.get('eligible_for_comparison', '-')}")
    print(f"Partidas alta            : {comparison.get('high_contest_matches', '-')}")
    print(f"Partidas menor           : {comparison.get('lower_contest_matches', '-')}")
    print(f"Delta                    : {comparison.get('placement_delta', '-')}")

    print("\nPRESSÃO RECORRENTE")
    print("-" * 108)
    for item in recurring.get("units", [])[:5]:
        print(f"Unidade: {item.get('item_id')} · {item.get('matches_observed')} partidas · {item.get('match_rate')}%")
    for item in recurring.get("traits", [])[:5]:
        print(f"Trait  : {item.get('item_id')} · {item.get('matches_observed')} partidas · {item.get('match_rate')}%")

    print("\nCOACH")
    print("-" * 108)
    for item in coach.get("observations", []):
        print("-", item)

    print("\n" + "=" * 108)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde '#26 CONTESTAÇÃO AVANÇADA - API REAL' até o final.")
    print("=" * 108)

if __name__ == "__main__":
    main()
