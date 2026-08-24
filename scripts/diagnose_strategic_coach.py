from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from partner_platform.services.api_client import (
    DashboardApiClient,
)
from partner_platform.intelligence.strategic_coach_messages import (
    build_strategic_coach_messages,
)


def main() -> None:
    print("=" * 72)
    print("TFT INSIGHT - STRATEGIC COACH DIAGNOSTIC")
    print("=" * 72)

    print(
        "\nEste diagnóstico usa o mesmo DashboardApiClient "
        "da Partner Platform."
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

    print("\n[1] Chamando comparação...")

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

    print(
        "[OK] resposta recebida"
    )

    print(
        "\nChaves principais recebidas:"
    )
    print(
        ", ".join(
            sorted(
                comparison.keys()
            )
        )
    )

    coach_context = comparison.get(
        "coach_context"
    )

    print("\n[2] coach_context")

    if not coach_context:
        print(
            "[ERRO] coach_context NÃO chegou "
            "na resposta da API."
        )
        print(
            "\nIsso indica que a rota de benchmark "
            "em execução ainda não está anexando "
            "o contexto estratégico."
        )
        return

    print(
        "[OK] coach_context recebido"
    )

    for section in (
        "composition",
        "contest",
        "economy",
    ):
        payload = coach_context.get(
            section
        )

        print(
            f"\n--- {section.upper()} ---"
        )

        if not payload:
            print(
                "[ERRO] seção ausente/vazia"
            )
            continue

        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )

    print(
        "\n[3] strategic_messages"
    )

    messages = (
        build_strategic_coach_messages(
            coach_context
        )
    )

    print(
        f"Quantidade gerada: {len(messages)}"
    )

    if not messages:
        print(
            "[ERRO] coach_context chegou, "
            "mas nenhuma mensagem estratégica "
            "foi gerada."
        )
        return

    for index, message in enumerate(
        messages,
        start=1,
    ):
        print(
            f"\nMensagem {index}"
        )
        print(
            json.dumps(
                message,
                ensure_ascii=False,
                indent=2,
            )
        )

    print(
        "\n" + "=" * 72
    )
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Copie o resultado desde [2] coach_context "
        "até o final e envie para o ChatGPT."
    )
    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()
