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

    payload = client.economy_intelligence(
        game_name=game_name,
        tag_line=tag_line,
        match_count=30,
    )

    summary = payload.get("summary", {}) or {}
    latest = payload.get("latest", {}) or {}
    distribution = payload.get("distribution", {}) or {}
    trend = payload.get("recent_trend", {}) or {}
    comparison = payload.get("placement_comparison", {}) or {}
    coach = payload.get("coach", {}) or {}

    print()
    print("=" * 108)
    print("#27 ECONOMIA AVANÇADA - API REAL")
    print("=" * 108)
    print(f"Jogador                  : {game_name}#{tag_line}")
    print(f"Partidas                 : {summary.get('matches_analyzed', '-')}")
    print(f"Score                    : {summary.get('score', '-')}")
    print(f"Classificação            : {summary.get('label', '-')}")
    print(f"Nível médio              : {summary.get('average_level', '-')}")
    print(f"Ouro restante médio      : {summary.get('average_gold_left', '-')}")
    print(f"Nível 8+                 : {summary.get('level_8_rate', '-')}%")
    print(f"Nível 9+                 : {summary.get('level_9_rate', '-')}%")
    print(f"Nível baixo tardio       : {summary.get('low_level_late_rate', '-')}%")

    print()
    print("ÚLTIMA PARTIDA")
    print("-" * 108)
    print(f"Partida                  : {latest.get('match_id', '-')}")
    print(f"Colocação                : {latest.get('placement', '-')}")
    print(f"Nível                    : {latest.get('level', '-')}")
    print(f"Ouro                     : {latest.get('gold_left', '-')}")
    print(f"Round                    : {latest.get('last_round', '-')}")

    print()
    print("DISTRIBUIÇÃO")
    print("-" * 108)
    for key, value in distribution.items():
        print(f"{key:<28}: {value}")

    print()
    print("HISTÓRICO RECENTE")
    print("-" * 108)
    print(f"Sinal                    : {trend.get('signal', '-')}")
    print(f"Nível                    : {trend.get('previous_average_level', '-')} -> {trend.get('recent_average_level', '-')}")
    print(f"Ouro                     : {trend.get('previous_average_gold_left', '-')} -> {trend.get('recent_average_gold_left', '-')}")
    print(f"Colocação                : {trend.get('previous_average_placement', '-')} -> {trend.get('recent_average_placement', '-')}")

    print()
    print("NÍVEL 9+ E RESULTADO")
    print("-" * 108)
    print(f"Elegível                 : {comparison.get('eligible_for_comparison', '-')}")
    print(f"Nível 9+                 : {comparison.get('level_9_plus_matches', '-')} partidas · média {comparison.get('level_9_plus_average_placement', '-')}")
    print(f"Abaixo de 9              : {comparison.get('below_level_9_matches', '-')} partidas · média {comparison.get('below_level_9_average_placement', '-')}")
    print(f"Delta                    : {comparison.get('placement_delta', '-')}")

    print()
    print("COACH")
    print("-" * 108)
    for observation in coach.get("observations", []):
        print("-", observation)

    print()
    print("=" * 108)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde '#27 ECONOMIA AVANÇADA - API REAL' até o final.")
    print("=" * 108)


if __name__ == "__main__":
    main()
