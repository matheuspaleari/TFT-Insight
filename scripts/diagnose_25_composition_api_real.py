from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from partner_platform.services.api_client import (
    DashboardApiClient,
)


def main() -> None:
    game_name = input(
        "Riot ID (Game Name): "
    ).strip()
    tag_line = input(
        "Tag: "
    ).strip()

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

    payload = (
        client.composition_intelligence(
            game_name=game_name,
            tag_line=tag_line,
            match_count=30,
        )
    )

    summary = payload.get(
        "summary",
        {},
    ) or {}

    most = payload.get(
        "most_used",
        {},
    ) or {}

    best = payload.get(
        "best_supported",
    )

    print()
    print("=" * 104)
    print(
        "#25 COMPOSIÇÕES AVANÇADAS - API REAL"
    )
    print("=" * 104)

    print(
        f"Jogador              : "
        f"{game_name}#{tag_line}"
    )
    print(
        f"Partidas             : "
        f"{summary.get('matches_analyzed', '-')}"
    )
    print(
        f"Composições          : "
        f"{summary.get('unique_compositions', '-')}"
    )
    print(
        f"Diversidade          : "
        f"{summary.get('diversity_rate', '-')}%"
    )
    print(
        f"Repetição            : "
        f"{summary.get('repetition_rate', '-')}%"
    )

    print()
    print(
        "MAIS USADA"
    )
    print(
        "-" * 104
    )
    print(
        f"Carry                : "
        f"{most.get('carry_character_id', '-')}"
    )
    print(
        f"Partidas             : "
        f"{most.get('matches_played', '-')}"
    )
    print(
        f"Elegível comparação  : "
        f"{most.get('eligible_for_comparison', '-')}"
    )
    print(
        f"Confiança            : "
        f"{(most.get('statistical_confidence') or {}).get('level', '-')}"
    )

    print()
    print(
        "MELHOR COM AMOSTRA MÍNIMA"
    )
    print(
        "-" * 104
    )

    if isinstance(
        best,
        dict,
    ):
        print(
            f"Carry                : "
            f"{best.get('carry_character_id', '-')}"
        )
        print(
            f"Média                : "
            f"{best.get('average_placement', '-')}"
        )
        print(
            f"Top4                 : "
            f"{best.get('top4_rate', '-')}%"
        )
    else:
        print(
            "Nenhuma composição elegível."
        )

    print()
    print(
        "COACH"
    )
    print(
        "-" * 104
    )

    coach = payload.get(
        "coach",
        {},
    ) or {}

    print(
        coach.get(
            "most_used_reading",
            "-",
        )
    )

    print()
    print(
        "SUPPORT PÚBLICO"
    )
    print(
        "-" * 104
    )

    has_support = any(
        "support_character_id"
        in profile
        for profile in payload.get(
            "compositions",
            [],
        )
        if isinstance(
            profile,
            dict,
        )
    )

    print(
        f"Exposto na API pública : "
        f"{has_support}"
    )

    print()
    print("=" * 104)
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Se API + UI estiverem corretas, #25 pode ser fechado."
    )
    print("=" * 104)


if __name__ == "__main__":
    main()
