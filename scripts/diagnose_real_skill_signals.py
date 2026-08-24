from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from partner_platform.services.api_client import DashboardApiClient
from src.learning.services.habit_engine import HabitEngine
from src.learning.services.habit_skill_mapping_service import (
    HabitSkillMappingService,
)


LEVEL_LABELS = {
    0: "Não avaliada",
    1: "Iniciante",
    2: "Em desenvolvimento",
    3: "Competente",
    4: "Avançada",
    5: "Dominada",
}


def main() -> None:
    print("=" * 78)
    print("TFT INSIGHT - REAL SKILL SIGNALS DIAGNOSTIC")
    print("=" * 78)

    riot_id = input("Riot ID (Game Name): ").strip()
    tag = input("Tag: ").strip()
    benchmark_id = input(
        "Benchmark ID [advanced]: "
    ).strip() or "advanced"
    matches_raw = input(
        "Quantidade de partidas [30]: "
    ).strip() or "30"
    api_base_url = input(
        "API Base URL [http://127.0.0.1:8000]: "
    ).strip() or "http://127.0.0.1:8000"

    try:
        match_count = int(matches_raw)
    except ValueError:
        match_count = 30

    client = DashboardApiClient(
        base_url=api_base_url,
        api_key=None,
    )

    comparison = client.compare_player_to_benchmark(
        benchmark_id=benchmark_id,
        game_name=riot_id,
        tag_line=tag,
        match_count=match_count,
    )

    coach_context = comparison.get(
        "coach_context"
    )

    if not coach_context:
        print("[ERRO] coach_context não retornado.")
        return

    habits = HabitEngine.detect(
        coach_context=coach_context
    )

    signals = HabitSkillMappingService.map(
        habits=habits
    )

    print()
    print(f"Habits detectados: {len(habits)}")
    print(f"Skill Signals    : {len(signals)}")

    for index, signal in enumerate(
        signals,
        start=1,
    ):
        print()
        print("-" * 78)
        print(f"SKILL SIGNAL {index}")
        print("-" * 78)
        print(f"Skill ID     : {signal.skill_id}")
        print(f"Nome         : {signal.skill_label}")
        print(f"Direção      : {signal.direction}")
        print(f"Confiança    : {signal.confidence:.2f}%")
        print(
            "Avaliável    : "
            + ("Sim" if signal.assessable else "Não")
        )
        print(
            "Nível sugerido: "
            + (
                LEVEL_LABELS[
                    int(signal.level_hint)
                ]
                if signal.level_hint is not None
                else "-"
            )
        )
        print(
            "Habits       : "
            + ", ".join(signal.habit_ids)
        )
        print()
        print("Interpretação:")
        print(signal.interpretation)

        if signal.limitations:
            print()
            print("Limitações:")
            for limitation in signal.limitations:
                print(f"  - {limitation}")

    print()
    print("=" * 78)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie todos os SKILL SIGNALS.")
    print("=" * 78)


if __name__ == "__main__":
    main()
