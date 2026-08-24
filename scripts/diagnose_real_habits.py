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


from partner_platform.services.api_client import (
    DashboardApiClient,
)
from src.learning.services.habit_engine import (
    HabitEngine,
)


def _format_evidence(
    evidence,
) -> str:
    value = evidence.value

    if isinstance(value, float):
        value_text = f"{value:.2f}"
    else:
        value_text = str(value)

    if evidence.unit:
        value_text = (
            f"{value_text} {evidence.unit}"
        )

    return (
        f"{evidence.label}: "
        f"{value_text}"
    )


def main() -> None:
    print("=" * 76)
    print("TFT INSIGHT - REAL HABITS DIAGNOSTIC")
    print("=" * 76)

    print(
        "\nEste diagnóstico usa o mesmo coach_context "
        "recebido pela página de Benchmark."
    )

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
        match_count = int(
            matches_raw
        )
    except ValueError:
        match_count = 30

    client = DashboardApiClient(
        base_url=api_base_url,
        api_key=None,
    )

    print(
        "\n[1] Buscando coach_context real..."
    )

    try:
        comparison = (
            client.compare_player_to_benchmark(
                benchmark_id=benchmark_id,
                game_name=riot_id,
                tag_line=tag,
                match_count=match_count,
            )
        )
    except Exception as exc:
        print(
            "[ERRO] Falha ao chamar a API:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    coach_context = comparison.get(
        "coach_context"
    )

    if not coach_context:
        print(
            "[ERRO] coach_context não foi retornado."
        )
        return

    print(
        "[OK] coach_context recebido"
    )

    print(
        "\n[2] Resumo do contexto estratégico"
    )

    for section in (
        "contest",
        "composition",
        "economy",
    ):
        payload = coach_context.get(
            section,
            {},
        )

        print(
            f"\n--- {section.upper()} ---"
        )

        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )

    print(
        "\n[3] Detectando hábitos..."
    )

    habits = HabitEngine.detect(
        coach_context=coach_context
    )

    print(
        f"Quantidade detectada: {len(habits)}"
    )

    if not habits:
        print(
            "\nNenhum hábito foi declarado para esta amostra."
        )
        print(
            "Isso pode ser correto se os sinais forem fracos "
            "ou a amostra não atingir o mínimo exigido."
        )
        return

    for index, habit in enumerate(
        habits,
        start=1,
    ):
        print()
        print(
            "-" * 76
        )
        print(
            f"HABIT {index}"
        )
        print(
            "-" * 76
        )

        print(
            f"ID           : {habit.habit_id}"
        )
        print(
            f"Categoria    : {habit.category}"
        )
        print(
            f"Nome         : {habit.label}"
        )
        print(
            f"Direção      : {habit.direction}"
        )
        print(
            f"Status       : {habit.status}"
        )
        print(
            f"Confiança    : {habit.confidence:.2f}%"
        )
        print(
            f"Skill ID     : {habit.related_skill_id or '-'}"
        )
        print(
            f"Skill hint   : {habit.related_skill_hint or '-'}"
        )

        print(
            "\nInterpretação:"
        )
        print(
            habit.interpretation
        )

        print(
            "\nEvidências:"
        )

        for evidence in habit.evidence:
            print(
                "  - "
                + _format_evidence(
                    evidence
                )
            )

    print()
    print(
        "=" * 76
    )
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Envie o resultado da seção [3] até o final."
    )
    print(
        "=" * 76
    )


if __name__ == "__main__":
    main()
