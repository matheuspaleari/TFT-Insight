from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_platform.services.api_client import DashboardApiClient


def main() -> None:
    print("=" * 88)
    print("TFT INSIGHT - COACH CONTEXT FUSION V1 - REAL")
    print("=" * 88)

    game_name = input("Riot ID (Game Name): ").strip()
    tag = input("Tag: ").strip()
    matches = int(
        input("Partidas [30]: ").strip()
        or "30"
    )
    benchmark_id = input(
        "Benchmark [advanced]: "
    ).strip() or "advanced"

    client = DashboardApiClient(
        base_url=os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        api_key=os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ),
    )

    analysis = client.analyze_player(
        game_name=game_name,
        tag_line=tag,
        match_count=matches,
        learn=True,
    )

    comparison = client.compare_player_to_benchmark(
        benchmark_id=benchmark_id,
        game_name=game_name,
        tag_line=tag,
        match_count=matches,
    )

    fusion = comparison.get(
        "coach_fusion",
        {},
    )

    print()
    print("=" * 88)
    print("COACH CONTEXT FUSION")
    print("=" * 88)

    competitive = fusion.get(
        "competitive_context",
        {},
    )
    problem = fusion.get(
        "problem_observed",
        {},
    )
    focus = fusion.get(
        "training_focus",
        {},
    )
    strength = fusion.get(
        "strength_to_preserve",
        {},
    )

    print(
        "Grupo competitivo    : "
        f"{competitive.get('group_label', '-')}"
    )
    print(
        "Faixa no grupo       : "
        f"{competitive.get('spectrum_band', '-')}"
    )
    print(
        "Problema observado   : "
        f"{problem.get('title', '-')}"
    )
    print(
        "Foco de treino       : "
        f"{focus.get('mission_title', '-')}"
    )
    print(
        "Próxima ação         : "
        f"{focus.get('next_action', '-')}"
    )
    print(
        "Ponto forte          : "
        f"{strength.get('skill_label', '-') if isinstance(strength, dict) else '-'}"
    )

    print()
    print("SINAIS DE APOIO")
    print("-" * 88)

    for item in fusion.get(
        "supporting_signals",
        [],
    ):
        print(
            f"- {item.get('label', '-')}: "
            f"{item.get('action') or item.get('explanation') or '-'}"
        )

    print()
    print("PROTEÇÕES")
    print("-" * 88)

    for key, value in fusion.get(
        "protections",
        {},
    ).items():
        print(f"{key:<30}: {value}")

    print()
    print("=" * 88)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'COACH CONTEXT FUSION' até o final.")
    print("=" * 88)


if __name__ == "__main__":
    main()
