from __future__ import annotations

import json
import sys
from pathlib import Path

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


from partner_platform.services.api_client import DashboardApiClient
from src.learning.services.habit_engine import HabitEngine


def main() -> None:
    print("=" * 76)
    print("TFT INSIGHT - HABIT ENGINE V1.1 DIAGNOSTIC")
    print("=" * 76)

    riot_id = input(
        "Riot ID (Game Name): "
    ).strip()

    tag = input(
        "Tag: "
    ).strip()

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

    print("\n[1] Buscando coach_context real...")

    try:
        comparison = client.compare_player_to_benchmark(
            benchmark_id=benchmark_id,
            game_name=riot_id,
            tag_line=tag,
            match_count=match_count,
        )
    except Exception as exc:
        print("[ERRO] Falha ao chamar a API:")
        print(f"{type(exc).__name__}: {exc}")
        return

    coach_context = comparison.get(
        "coach_context"
    )

    if not coach_context:
        print("[ERRO] coach_context não foi retornado.")
        return

    print("[OK] coach_context recebido")

    print("\n[2] Habits declarados")
    habits = HabitEngine.detect(
        coach_context=coach_context
    )

    if not habits:
        print("Nenhum Habit declarado.")
    else:
        for habit in habits:
            print(
                f"- {habit.habit_id} | "
                f"{habit.direction} | "
                f"{habit.status} | "
                f"{habit.confidence:.2f}%"
            )

    print("\n[3] Diagnóstico por categoria")
    diagnostics = HabitEngine.diagnose(
        coach_context=coach_context
    )

    for diagnostic in diagnostics:
        print()
        print("-" * 76)
        print(
            f"CATEGORIA: {diagnostic.category.upper()}"
        )
        print(
            f"Status   : {diagnostic.status}"
        )
        print(
            f"Habit    : {diagnostic.declared_habit_id or '-'}"
        )
        print(
            "Motivo   : "
            + diagnostic.explanation
        )
        print("Checks:")
        for check in diagnostic.checks:
            print(
                "  - "
                + check
            )

    print()
    print("=" * 76)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie principalmente a seção COMPOSITION e, "
        "se quiser, o restante da seção [3]."
    )
    print("=" * 76)


if __name__ == "__main__":
    main()
